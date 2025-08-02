"use client"

import { useState, useMemo, useCallback } from 'react'

export interface SortConfig {
  key: string
  direction: 'asc' | 'desc'
}

export interface FilterConfig {
  [key: string]: string | number | boolean | undefined
}

interface UseFormTableOptions<T> {
  data: T[]
  itemsPerPage?: number
  defaultSort?: SortConfig
  searchableFields?: (keyof T)[]
}

export function useFormTable<T extends Record<string, any>>({
  data,
  itemsPerPage = 10,
  defaultSort,
  searchableFields = []
}: UseFormTableOptions<T>) {
  const [currentPage, setCurrentPage] = useState(1)
  const [sortConfig, setSortConfig] = useState<SortConfig | undefined>(defaultSort)
  const [filters, setFilters] = useState<FilterConfig>({})
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedItems, setSelectedItems] = useState<Set<string | number>>(new Set())

  // Filter data
  const filteredData = useMemo(() => {
    let filtered = [...data]

    // Apply search
    if (searchTerm && searchableFields.length > 0) {
      filtered = filtered.filter(item =>
        searchableFields.some(field =>
          String(item[field]).toLowerCase().includes(searchTerm.toLowerCase())
        )
      )
    }

    // Apply filters
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== '') {
        filtered = filtered.filter(item => {
          const itemValue = item[key]
          if (typeof value === 'boolean') {
            return itemValue === value
          }
          return String(itemValue).toLowerCase().includes(String(value).toLowerCase())
        })
      }
    })

    return filtered
  }, [data, searchTerm, searchableFields, filters])

  // Sort data
  const sortedData = useMemo(() => {
    if (!sortConfig) return filteredData

    return [...filteredData].sort((a, b) => {
      const aValue = a[sortConfig.key]
      const bValue = b[sortConfig.key]

      if (aValue < bValue) {
        return sortConfig.direction === 'asc' ? -1 : 1
      }
      if (aValue > bValue) {
        return sortConfig.direction === 'asc' ? 1 : -1
      }
      return 0
    })
  }, [filteredData, sortConfig])

  // Paginate data
  const paginatedData = useMemo(() => {
    const startIndex = (currentPage - 1) * itemsPerPage
    return sortedData.slice(startIndex, startIndex + itemsPerPage)
  }, [sortedData, currentPage, itemsPerPage])

  const totalPages = Math.ceil(filteredData.length / itemsPerPage)

  // Handlers
  const handleSort = useCallback((key: string) => {
    setSortConfig(current => {
      if (!current || current.key !== key) {
        return { key, direction: 'asc' }
      }
      if (current.direction === 'asc') {
        return { key, direction: 'desc' }
      }
      return undefined
    })
  }, [])

  const handleFilter = useCallback((key: string, value: any) => {
    setFilters(current => ({
      ...current,
      [key]: value
    }))
    setCurrentPage(1)
  }, [])

  const clearFilters = useCallback(() => {
    setFilters({})
    setSearchTerm('')
    setCurrentPage(1)
  }, [])

  const handleSelectItem = useCallback((id: string | number) => {
    setSelectedItems(current => {
      const newSet = new Set(current)
      if (newSet.has(id)) {
        newSet.delete(id)
      } else {
        newSet.add(id)
      }
      return newSet
    })
  }, [])

  const handleSelectAll = useCallback((ids: (string | number)[]) => {
    setSelectedItems(new Set(ids))
  }, [])

  const clearSelection = useCallback(() => {
    setSelectedItems(new Set())
  }, [])

  return {
    // Data
    data: paginatedData,
    filteredData,
    totalItems: filteredData.length,
    
    // Pagination
    currentPage,
    totalPages,
    setCurrentPage,
    
    // Sorting
    sortConfig,
    handleSort,
    
    // Filtering
    filters,
    searchTerm,
    setSearchTerm,
    handleFilter,
    clearFilters,
    
    // Selection
    selectedItems,
    handleSelectItem,
    handleSelectAll,
    clearSelection,
    isSelected: (id: string | number) => selectedItems.has(id),
    
    // Utilities
    hasFilters: Object.keys(filters).length > 0 || searchTerm !== '',
    isEmpty: paginatedData.length === 0
  }
}