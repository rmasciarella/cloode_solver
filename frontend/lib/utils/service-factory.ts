/**
 * Service Factory Utility
 * 
 * Provides lazy initialization for service singletons to prevent
 * issues in serverless environments where global state can persist
 * between function invocations.
 */

type ServiceConstructor<T> = new (...args: any[]) => T

interface ServiceCache {
  [key: string]: any
}

const serviceCache: ServiceCache = {}

/**
 * Creates a lazy-initialized service singleton
 * Services are only instantiated on first use, not at module load time
 */
export function createLazyService<T>(
  serviceName: string,
  ServiceClass: ServiceConstructor<T>,
  ...constructorArgs: any[]
): () => T {
  return () => {
    if (!serviceCache[serviceName]) {
      serviceCache[serviceName] = new ServiceClass(...constructorArgs)
    }
    return serviceCache[serviceName] as T
  }
}

/**
 * Creates a proxy that lazily initializes the service on first property access
 * This maintains backward compatibility with existing code that expects an object
 */
export function createLazyServiceProxy<T extends object>(
  serviceName: string,
  ServiceClass: ServiceConstructor<T>,
  ...constructorArgs: any[]
): T {
  const getService = createLazyService(serviceName, ServiceClass, ...constructorArgs)
  
  return new Proxy({} as T, {
    get(target, prop) {
      const service = getService()
      return service[prop as keyof T]
    },
    set(target, prop, value) {
      const service = getService()
      service[prop as keyof T] = value
      return true
    }
  })
}

/**
 * Clears the service cache - useful for testing or cleanup
 * In production, this should rarely be needed as serverless functions
 * are short-lived
 */
export function clearServiceCache() {
  Object.keys(serviceCache).forEach(key => {
    delete serviceCache[key]
  })
}

/**
 * Gets the current service cache size for monitoring
 */
export function getServiceCacheStats() {
  return {
    serviceCount: Object.keys(serviceCache).length,
    services: Object.keys(serviceCache)
  }
}