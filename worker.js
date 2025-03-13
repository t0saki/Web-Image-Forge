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
 * Cloudflare Worker for image optimization redirection
 * 
 * This worker:
 * 1. Intercepts image requests (e.g., b.com/file/c.jpg)
 * 2. Changes domain to d.com (e.g., d.com/file/c.jpg)
 * 3. Checks browser support for avif/webp
 * 4. Redirects to optimization service if supported, otherwise serves original
 * 5. Only processes GET requests without query parameters
 */

// Configuration parameters
const CONFIG = {
    // Target domain to change requests to
    targetDomain: ENV_TARGET_DOMAIM,

    // Converter service configuration
    converterService: {
        baseUrl: ENV_CONVERTER_SERVICE_BASE_URL,
        supportedFormats: ['avif', 'webp'] // In priority order
    },

    // HTTP redirect status code
    redirectStatusCode: 302
};

export default {
    async fetch(request, env, ctx) {
        const url = new URL(request.url);
        const pathname = url.pathname;

        // Create the modified URL with targetDomain
        const modifiedUrl = new URL(`${CONFIG.targetDomain}${pathname}`);
        
        // Copy any original query parameters to the modified URL
        for (const [key, value] of url.searchParams.entries()) {
            modifiedUrl.searchParams.set(key, value);
        }

        // Check if this is a GET request
        if (request.method !== 'GET') {
            return Response.redirect(modifiedUrl.toString(), CONFIG.redirectStatusCode);
        }
        
        // Check if the request has query parameters
        // If it does, just redirect to the original image with modified domain
        if (url.search !== '') {
            return Response.redirect(modifiedUrl.toString(), CONFIG.redirectStatusCode);
        }

        // Get the Accept header to check browser support
        const acceptHeader = request.headers.get('Accept') || '';

        // Determine the best supported format based on browser capabilities
        let format = null;
        for (const fmt of CONFIG.converterService.supportedFormats) {
            if (acceptHeader.includes(`image/${fmt}`)) {
                format = fmt;
                break;
            }
        }

        // If browser supports any of our supported formats, redirect to optimizer
        if (format) {
            // URL encode the modified URL to use with the converter
            const encodedUrl = encodeURIComponent(`${CONFIG.targetDomain}${pathname}`);
            const optimizerUrl = `${CONFIG.converterService.baseUrl}/${encodedUrl}?format=${format}`;

            return Response.redirect(optimizerUrl, CONFIG.redirectStatusCode);
        } else {
            // If no modern format is supported, redirect to the original image with modified domain
            return Response.redirect(modifiedUrl.toString(), CONFIG.redirectStatusCode);
        }
    },
};