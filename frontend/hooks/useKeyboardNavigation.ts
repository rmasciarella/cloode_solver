"use client"

import { useEffect, useCallback, RefObject } from 'react'

interface UseKeyboardNavigationOptions {
  onEscape?: () => void
  onEnter?: () => void
  onArrowUp?: () => void
  onArrowDown?: () => void
  onArrowLeft?: () => void
  onArrowRight?: () => void
  onTab?: (event: KeyboardEvent) => void
  onShiftTab?: (event: KeyboardEvent) => void
  containerRef?: RefObject<HTMLElement>
  enabled?: boolean
}

export function useKeyboardNavigation({
  onEscape,
  onEnter,
  onArrowUp,
  onArrowDown,
  onArrowLeft,
  onArrowRight,
  onTab,
  onShiftTab,
  containerRef,
  enabled = true
}: UseKeyboardNavigationOptions) {
  const handleKeyDown = useCallback((event: KeyboardEvent) => {
    if (!enabled) return

    switch (event.key) {
      case 'Escape':
        if (onEscape) {
          event.preventDefault()
          onEscape()
        }
        break
      
      case 'Enter':
        if (onEnter && !['TEXTAREA', 'INPUT'].includes((event.target as HTMLElement).tagName)) {
          event.preventDefault()
          onEnter()
        }
        break
      
      case 'ArrowUp':
        if (onArrowUp) {
          event.preventDefault()
          onArrowUp()
        }
        break
      
      case 'ArrowDown':
        if (onArrowDown) {
          event.preventDefault()
          onArrowDown()
        }
        break
      
      case 'ArrowLeft':
        if (onArrowLeft) {
          event.preventDefault()
          onArrowLeft()
        }
        break
      
      case 'ArrowRight':
        if (onArrowRight) {
          event.preventDefault()
          onArrowRight()
        }
        break
      
      case 'Tab':
        if (event.shiftKey && onShiftTab) {
          onShiftTab(event)
        } else if (!event.shiftKey && onTab) {
          onTab(event)
        }
        break
    }
  }, [enabled, onEscape, onEnter, onArrowUp, onArrowDown, onArrowLeft, onArrowRight, onTab, onShiftTab])

  useEffect(() => {
    if (!enabled) return

    const container = containerRef?.current || document
    const target = container === document ? window : container

    target.addEventListener('keydown', handleKeyDown as any)

    return () => {
      target.removeEventListener('keydown', handleKeyDown as any)
    }
  }, [handleKeyDown, containerRef, enabled])
}

// Hook for managing focus trap within a container
export function useFocusTrap(containerRef: RefObject<HTMLElement>, enabled = true) {
  useEffect(() => {
    if (!enabled || !containerRef.current) return

    const container = containerRef.current
    const focusableElements = container.querySelectorAll<HTMLElement>(
      'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])'
    )

    if (focusableElements.length === 0) return

    const firstElement = focusableElements[0]
    const lastElement = focusableElements[focusableElements.length - 1]

    const handleTab = (event: KeyboardEvent) => {
      if (event.key !== 'Tab') return

      if (event.shiftKey) {
        if (document.activeElement === firstElement) {
          event.preventDefault()
          lastElement.focus()
        }
      } else {
        if (document.activeElement === lastElement) {
          event.preventDefault()
          firstElement.focus()
        }
      }
    }

    container.addEventListener('keydown', handleTab)
    
    // Focus first element when trap is activated
    firstElement.focus()

    return () => {
      container.removeEventListener('keydown', handleTab)
    }
  }, [containerRef, enabled])
}

// Hook for arrow key navigation in lists/tables
export function useArrowKeyNavigation<T extends HTMLElement>(
  itemsRef: RefObject<T[]>,
  options: {
    orientation?: 'vertical' | 'horizontal' | 'both'
    loop?: boolean
    onSelect?: (index: number) => void
  } = {}
) {
  const { orientation = 'vertical', loop = true, onSelect } = options

  const navigate = useCallback((direction: 'up' | 'down' | 'left' | 'right') => {
    const items = itemsRef.current
    if (!items || items.length === 0) return

    const currentIndex = items.findIndex(item => item === document.activeElement)
    let nextIndex = currentIndex

    switch (direction) {
      case 'up':
        if (orientation === 'vertical' || orientation === 'both') {
          nextIndex = currentIndex > 0 ? currentIndex - 1 : (loop ? items.length - 1 : 0)
        }
        break
      
      case 'down':
        if (orientation === 'vertical' || orientation === 'both') {
          nextIndex = currentIndex < items.length - 1 ? currentIndex + 1 : (loop ? 0 : items.length - 1)
        }
        break
      
      case 'left':
        if (orientation === 'horizontal' || orientation === 'both') {
          nextIndex = currentIndex > 0 ? currentIndex - 1 : (loop ? items.length - 1 : 0)
        }
        break
      
      case 'right':
        if (orientation === 'horizontal' || orientation === 'both') {
          nextIndex = currentIndex < items.length - 1 ? currentIndex + 1 : (loop ? 0 : items.length - 1)
        }
        break
    }

    if (nextIndex !== currentIndex && items[nextIndex]) {
      items[nextIndex].focus()
      if (onSelect) {
        onSelect(nextIndex)
      }
    }
  }, [itemsRef, orientation, loop, onSelect])

  useKeyboardNavigation({
    onArrowUp: () => navigate('up'),
    onArrowDown: () => navigate('down'),
    onArrowLeft: () => navigate('left'),
    onArrowRight: () => navigate('right')
  })

  return { navigate }
}