/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,

  async headers() {
    if (process.env.NODE_ENV === 'production') {
      return [
        {
          source: '/:path*',
          headers: [
            { key: 'Access-Control-Allow-Credentials', value: 'true' },
            { key: 'Access-Control-Allow-Origin', value: '*' },
            { key: 'Access-Control-Allow-Methods', value: 'GET,DELETE,PATCH,POST,PUT' },
            { key: 'Access-Control-Allow-Headers', value: 'Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date' },
            {
              key: 'Content-Security-Policy',
              value: [
                "default-src 'self'",
                "worker-src 'self' blob:",
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' accounts.google.com *.googleusercontent.com apis.google.com www.gstatic.com *.google.com",
                "style-src 'self' 'unsafe-inline' *.googleapis.com *.cloudflare.com",
                "connect-src 'self' wss://* ws://* accounts.google.com *.googleapis.com *.google.com https://graph.microsoft.com *.microsoft.com",
                "frame-src 'self' accounts.google.com *.googleusercontent.com *.google.com drive.google.com",
                "form-src 'self' accounts.google.com",
                "img-src 'self' data: *.googleusercontent.com *.google.com"
              ].join('; ')
            },
            { key: 'X-Frame-Options', value: 'DENY' },
            { key: 'X-Content-Type-Options', value: 'nosniff' },
            { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
            { key: 'Permissions-Policy', value: 'camera=(), microphone=(), geolocation=()' }
          ]
        }
      ];
    }
    return []; // Return empty array in development
  },

  compiler: {
    // ✅ Enables SWC transformations (makes Next.js faster in dev mode)
    styledComponents: true,
  },

  webpack: (config, { dev, isServer }) => {
    // Add worker-loader configuration
    config.module.rules.unshift({
      test: /ace-builds.*worker-.*\.js$/,
      loader: "worker-loader",
      options: {
        name: "static/[hash].worker.js",
        publicPath: "/_next/",
      },
    });

    // ✅ Enable Webpack filesystem caching for faster builds
    config.cache = {
      type: "filesystem",
      buildDependencies: {
        config: [__filename],
      },
    };

    // Production optimizations
    if (!dev) {
      config.optimization.minimizer.push(
        new (require('terser-webpack-plugin'))({
          terserOptions: {
            compress: {
              drop_console: true,
            },
          },
        })
      );
      config.plugins.push(
        new (require('webpack')).DefinePlugin({
          'console.log': () => {},
          'console.warn': () => {},
          'console.error': () => {},
          'console.debug': () => {}
        })
      );
    }

    return config;
  },
};

module.exports = nextConfig;

