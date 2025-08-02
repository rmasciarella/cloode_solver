// UI Component Extension Hooks following Inventor Black's patterns

import React from 'react'

export interface UIHooks {
  // Component rendering hooks
  beforeRender: (_componentName: string, _props: any) => any | Promise<any>
  afterRender: (_componentName: string, element: React.ReactElement, _props: any) => React.ReactElement
  wrapComponent: (_componentName: string, element: React.ReactElement, _props: any) => React.ReactElement
  
  // Theme and styling hooks
  getThemeVariables: (_componentName: string, variant?: string) => Record<string, any>
  transformClassNames: (_componentName: string, classNames: string, _props: any) => string
  injectStyles: (_componentName: string, _props: any) => React.CSSProperties
  
  // Behavior hooks
  onComponentMount: (_componentName: string, ref: any, _props: any) => void
  onComponentUnmount: (_componentName: string, ref: any, _props: any) => void
  onPropsChange: (_componentName: string, prevProps: any, nextProps: any) => void
  
  // Event handling hooks
  interceptEvent: (_componentName: string, eventName: string, event: any, originalHandler?: Function) => boolean
  beforeEventHandler: (_componentName: string, eventName: string, event: any) => any
  afterEventHandler: (_componentName: string, eventName: string, event: any, result: any) => void
  
  // Accessibility hooks
  enhanceA11y: (_componentName: string, _props: any) => Record<string, any>
  announceChange: (_componentName: string, change: string, _props: any) => void
  
  // Validation and form hooks
  validateProps: (_componentName: string, _props: any) => string[]
  transformFormValue: (_componentName: string, fieldName: string, value: any) => any
  
  // Extension point hooks
  renderAdditionalContent: (_componentName: string, position: 'before' | 'after' | 'replace', _props: any) => React.ReactNode
  addContextMenuItems: (_componentName: string, _props: any) => Array<{label: string, action: Function, icon?: React.ReactNode}>
}

type UIHookHandler<K extends keyof UIHooks> = UIHooks[K]

class UIHookRegistry {
  private hooks: Map<keyof UIHooks, Array<{ handler: UIHookHandler<any>, priority: number, condition?: (_componentName: string, _props: any) => boolean }>> = new Map()
  
  register<K extends keyof UIHooks>(
    hookName: K,
    handler: UIHookHandler<K>,
    options: {
      priority?: number
      condition?: (_componentName: string, _props: any) => boolean
      components?: string[]
    } = {}
  ): () => void {
    const { priority = 10, condition, components } = options
    
    if (!this.hooks.has(hookName)) {
      this.hooks.set(hookName, [])
    }
    
    const effectiveCondition = components 
      ? (_componentName: string) => components.includes(_componentName)
      : condition
    
    const handlers = this.hooks.get(hookName)!
    const entry = { handler, priority, condition: effectiveCondition }
    handlers.push(entry)
    handlers.sort((a, b) => a.priority - b.priority)
    
    return () => {
      const index = handlers.findIndex(h => h.handler === handler)
      if (index > -1) handlers.splice(index, 1)
    }
  }
  
  async execute<K extends keyof UIHooks>(
    hookName: K,
    _componentName: string,
    ...args: any[]
  ): Promise<any> {
    const handlers = this.hooks.get(hookName) || []
    const applicableHandlers = handlers.filter(({ condition }) => 
      !condition || condition(_componentName, args[0])
    )
    
    if (applicableHandlers.length === 0) {
      return this.getDefaultReturn(hookName, args)
    }
    
    // Props transformation hooks (chain)
    if (['beforeRender', 'transformClassNames', 'enhanceA11y', 'transformFormValue'].includes(hookName as string)) {
      return applicableHandlers.reduce(async (result, { handler }) => {
        const data = await result
        return handler(_componentName, data, ...args.slice(1))
      }, Promise.resolve(args[0]))
    }
    
    // Component wrapping hooks (chain)
    if (['afterRender', 'wrapComponent'].includes(hookName as string)) {
      return applicableHandlers.reduce((element, { handler }) => {
        return handler(_componentName, element, ...args.slice(1))
      }, args[0] as React.ReactElement)
    }
    
    // Object merging hooks (merge all results)
    if (['getThemeVariables', 'injectStyles'].includes(hookName as string)) {
      const results = await Promise.all(
        applicableHandlers.map(({ handler }) => handler(_componentName, ...args))
      )
      return results.reduce((merged, result) => ({ ...merged, ...result }), {})
    }
    
    // Array merging hooks (concatenate results)
    if (['validateProps', 'addContextMenuItems'].includes(hookName as string)) {
      const results = await Promise.all(
        applicableHandlers.map(({ handler }) => handler(_componentName, ...args))
      )
      return results.flat()
    }
    
    // Content rendering hooks (render all)
    if (hookName === 'renderAdditionalContent') {
      const results = await Promise.all(
        applicableHandlers.map(({ handler }) => handler(_componentName, ...args))
      )
      return results.filter(Boolean)
    }
    
    // Event interception hooks (first false stops chain)
    if (hookName === 'interceptEvent') {
      for (const { handler } of applicableHandlers) {
        const result = await handler(_componentName, ...args)
        if (result === false) return false
      }
      return true
    }
    
    // Notification hooks (fire all)
    await Promise.all(
      applicableHandlers.map(({ handler }) => handler(_componentName, ...args))
    )
  }
  
  private getDefaultReturn(hookName: keyof UIHooks, args: any[]): any {
    switch (hookName) {
      case 'beforeRender':
      case 'transformClassNames':
      case 'transformFormValue':
        return args[0]
      case 'afterRender':
      case 'wrapComponent':
        return args[0]
      case 'getThemeVariables':
      case 'injectStyles':
      case 'enhanceA11y':
        return {}
      case 'validateProps':
      case 'addContextMenuItems':
        return []
      case 'interceptEvent':
        return true
      case 'renderAdditionalContent':
        return null
      default:
        return undefined
    }
  }
}

export const uiRegistry = new UIHookRegistry()

// Higher-order component to add hook support to existing components
export function withUIHooks<P extends object>(
  componentName: string,
  WrappedComponent: React.ComponentType<P>
): React.ForwardRefExoticComponent<React.PropsWithoutRef<P> & React.RefAttributes<any>> {
  return React.forwardRef<any, P>((_props, ref) => {
    const [enhancedProps, setEnhancedProps] = React.useState(_props)
    const componentRef = React.useRef<any>(null)
    
    // Merge forwarded ref with internal ref
    const mergedRef = React.useCallback((node: any) => {
      componentRef.current = node
      if (typeof ref === 'function') {
        ref(node)
      } else if (ref) {
        ref.current = node
      }
    }, [ref])
    
    React.useEffect(() => {
      const processProps = async () => {
        // Execute beforeRender hook
        const modifiedProps = await uiRegistry.execute('beforeRender', _componentName, _props)
        
        // Enhance accessibility
        const a11yProps = await uiRegistry.execute('enhanceA11y', _componentName, modifiedProps)
        
        // Validate props
        const validationErrors = await uiRegistry.execute('validateProps', _componentName, modifiedProps)
        if (validationErrors.length > 0) {
          console.warn(`[${_componentName}] Validation errors:`, validationErrors)
        }
        
        setEnhancedProps({ ...modifiedProps, ...a11yProps })
      }
      
      processProps()
    }, [props])
    
    React.useEffect(() => {
      // Component mount hook
      uiRegistry.execute('onComponentMount', _componentName, componentRef.current, enhancedProps)
      
      return () => {
        // Component unmount hook
        uiRegistry.execute('onComponentUnmount', _componentName, componentRef.current, enhancedProps)
      }
    }, [enhancedProps])
    
    React.useEffect(() => {
      // Props change hook
      uiRegistry.execute('onPropsChange', _componentName, _props, enhancedProps)
    }, [props, enhancedProps])
    
    // Get theme variables and inject styles
    const [themeVars, setThemeVars] = React.useState<Record<string, any>>({})
    const [injectedStyles, setInjectedStyles] = React.useState<React.CSSProperties>({})
    const [transformedClassName, setTransformedClassName] = React.useState<string | undefined>()
    
    React.useEffect(() => {
      const loadThemeAndStyles = async () => {
        const theme = await uiRegistry.execute('getThemeVariables', _componentName, (enhancedProps as any).variant)
        const styles = await uiRegistry.execute('injectStyles', _componentName, enhancedProps)
        setThemeVars(theme || {})
        setInjectedStyles(styles || {})
      }
      loadThemeAndStyles()
    }, [(enhancedProps as any).variant, enhancedProps])
    
    React.useEffect(() => {
      const loadClassName = async () => {
        if ('className' in enhancedProps) {
          const className = await uiRegistry.execute('transformClassNames', _componentName, (enhancedProps as any).className as string, enhancedProps)
          setTransformedClassName(className)
        } else {
          setTransformedClassName(undefined)
        }
      }
      loadClassName()
    }, [enhancedProps])
    
    // Create enhanced event handlers
    const createEnhancedHandler = React.useCallback((eventName: string, originalHandler?: Function) => {
      return async (event: any) => {
        // Check if event should be intercepted
        const shouldContinue = await uiRegistry.execute('interceptEvent', _componentName, eventName, event, originalHandler)
        if (!shouldContinue) return
        
        // Execute beforeEventHandler
        const modifiedEvent = await uiRegistry.execute('beforeEventHandler', _componentName, eventName, event)
        
        // Execute original handler if provided
        let result
        if (originalHandler) {
          result = await originalHandler(modifiedEvent || event)
        }
        
        // Execute afterEventHandler
        await uiRegistry.execute('afterEventHandler', _componentName, eventName, modifiedEvent || event, result)
        
        return result
      }
    }, [componentName])
    
    // Enhance event props
    const enhancedEventProps = React.useMemo(() => {
      const eventProps: any = {}
      Object.keys(enhancedProps).forEach(key => {
        if (key.startsWith('on') && typeof (enhancedProps as any)[key] === 'function') {
          const eventName = key.slice(2).toLowerCase()
          eventProps[key] = createEnhancedHandler(eventName, (enhancedProps as any)[key])
        }
      })
      return eventProps
    }, [enhancedProps, createEnhancedHandler])
    
    // State for async-rendered elements
    const [finalElement, setFinalElement] = React.useState<React.ReactElement | null>(null)
    
    React.useEffect(() => {
      const renderEnhancedElement = async () => {
        // Render component with all enhancements
        let element = React.createElement(WrappedComponent, {
          ...enhancedProps,
          ...enhancedEventProps,
          ref: mergedRef,
          className: transformedClassName || (enhancedProps as any).className,
          style: { ...(enhancedProps as any).style, ...injectedStyles }
        })
        
        // Execute afterRender and wrapComponent hooks
        element = await uiRegistry.execute('afterRender', _componentName, element, enhancedProps) as React.ReactElement || element
        element = await uiRegistry.execute('wrapComponent', _componentName, element, enhancedProps) as React.ReactElement || element
        
        // Render additional content
        const beforeContent = await uiRegistry.execute('renderAdditionalContent', _componentName, 'before', enhancedProps)
        const afterContent = await uiRegistry.execute('renderAdditionalContent', _componentName, 'after', enhancedProps)
        const replaceContent = await uiRegistry.execute('renderAdditionalContent', _componentName, 'replace', enhancedProps)
        
        if (replaceContent) {
          setFinalElement(replaceContent as React.ReactElement)
          return
        }
        
        setFinalElement(
          <React.Fragment>
            {beforeContent}
            {element}
            {afterContent}
          </React.Fragment>
        )
      }
      
      renderEnhancedElement()
    }, [enhancedProps, enhancedEventProps, transformedClassName, injectedStyles, mergedRef])
    
    // Return loading state while async operations complete
    if (!finalElement) {
      return React.createElement(WrappedComponent, {
        ...enhancedProps,
        ref: mergedRef
      } as any)
    }
    
    return finalElement
  })
}

// Hook for accessing UI registry in components
export function useUIHooks() {
  return {
    register: uiRegistry.register.bind(uiRegistry),
    execute: uiRegistry.execute.bind(uiRegistry)
  }
}

// Common UI hook patterns
export function createUIHookPatterns() {
  // Debug overlay for development
  if (process.env.NODE_ENV === 'development') {
    uiRegistry.register('wrapComponent', (_componentName, element, _props) => {
      return (
        <div data-component={_componentName} title={`Component: ${_componentName}`}>
          {element}
        </div>
      )
    }, { priority: 1000 })
  }
  
  // Focus management
  uiRegistry.register('onComponentMount', (_componentName, ref, _props) => {
    if (props.autoFocus && ref && ref.focus) {
      setTimeout(() => ref.focus(), 0)
    }
  }, { components: ['Input', 'Textarea', 'Select'] })
  
  // Keyboard navigation
  uiRegistry.register('beforeEventHandler', (_componentName, eventName, event) => {
    if (eventName === 'keydown' && event.key === 'Escape') {
      const activeElement = document.activeElement as HTMLElement
      if (activeElement && activeElement.blur) {
        activeElement.blur()
      }
    }
    return event
  })
  
  return uiRegistry
}