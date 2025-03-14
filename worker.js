/**
 * Welcome to Cloudflare Workers! This is your first worker.
 *
 * - Run "npm run dev" in your terminal to start a development server
 * - Open a browser tab at http://localhost:8787/ to see your worker in action
 * - Run "npm run deploy" to publish your worker
 *
 * Learn more at https://developers.cloudflare.com/workers/
 */

/**
 * Cloudflare Worker for image optimization proxy
 * 
 * This worker:
 * 1. Intercepts image requests (e.g., b.com/file/c.jpg)
 * 2. Forwards request to optimization service with original Accept header
 * 3. The optimization service will determine format support
 * 4. Returns optimized image directly to user without redirects
 * 5. Handles requests with or without query parameters
 */

// Configuration parameters
const CONFIG = {
    // Target domain to change requests to
    targetDomain: ENV_TARGET_DOMAIM,

    // Converter service configuration
    converterService: {
        baseUrl: ENV_CONVERTER_SERVICE_BASE_URL,
        apiKey: ENV_API_KEY || '' // API Key for authentication
    },

    // Cache settings
    cacheControlMaxAge: 86400 * 30 // 30 days in seconds
};

export default {
    async fetch(request, env, ctx) {
        const url = new URL(request.url);
        const pathname = url.pathname;

        // Create the modified URL with targetDomain for original content
        const modifiedUrl = new URL(`${CONFIG.targetDomain}${pathname}`);
        
        // Copy any original query parameters to the modified URL
        for (const [key, value] of url.searchParams.entries()) {
            modifiedUrl.searchParams.set(key, value);
        }

        // Only process GET requests
        if (request.method !== 'GET') {
            // For non-GET requests, proxy to original content
            return await fetchAndReturnResponse(modifiedUrl.toString());
        }

        // Create the optimizer URL
        const encodedUrl = encodeURIComponent(`${CONFIG.targetDomain}${pathname}`);
        const optimizerUrl = `${CONFIG.converterService.baseUrl}/${encodedUrl}`;
        
        // Proxy the request to the optimizer with API key and original headers
        return await fetchAndReturnResponse(optimizerUrl, true, request.headers);
    },
};

/**
 * Fetches a resource and returns it as a Response
 * @param {string} url - The URL to fetch
 * @param {boolean} useApiKey - Whether to include API key in the request
 * @param {Headers} originalHeaders - Original request headers to forward
 * @returns {Promise<Response>} - The response to return to the client
 */
async function fetchAndReturnResponse(url, useApiKey = false, originalHeaders = null) {
    try {
        // Prepare fetch options
        const fetchOptions = {
            cf: {
                // Cache using the Cloudflare CDN
                cacheTtl: CONFIG.cacheControlMaxAge,
                cacheEverything: true,
            },
            headers: {}
        };
        
        // Add API key if needed and available
        if (useApiKey && CONFIG.converterService.apiKey) {
            fetchOptions.headers['X-API-Key'] = CONFIG.converterService.apiKey;
        }
        
        // Forward important headers from original request
        if (originalHeaders) {
            // Forward Accept header for format detection
            const acceptHeader = originalHeaders.get('Accept');
            if (acceptHeader) {
                fetchOptions.headers['Accept'] = acceptHeader;
            }
            
            // Forward User-Agent for potential server-side decisions
            const userAgent = originalHeaders.get('User-Agent');
            if (userAgent) {
                fetchOptions.headers['User-Agent'] = userAgent;
            }
        }
        
        // Fetch the resource
        const response = await fetch(url, fetchOptions);
        
        // If the response was successful
        if (response.ok) {
            // Create a new response with the same body
            const newResponse = new Response(response.body, response);
            
            // Setup cache control headers
            newResponse.headers.set('Cache-Control', `public, max-age=${CONFIG.cacheControlMaxAge}`);
            
            // Return the modified response
            return newResponse;
        }
        
        // If fetch failed, return the error response
        return response;
    } catch (error) {
        // In case of a network error, return a 502 Bad Gateway
        return new Response(`Proxy error: ${error.message}`, { status: 502 });
    }
}