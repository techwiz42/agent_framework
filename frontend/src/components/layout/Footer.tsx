// src/components/layout/Footer.tsx
export function Footer() {
  return (
    <footer className="bg-white border-t mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div className="flex justify-center items-center">
          <div className="flex items-center gap-6">
            <p className="text-sm text-gray-500">
              © {new Date().getFullYear()} Agent Framework
            </p>
            <a 
              href="mailto:thetechwizard42@gmail.com"
              className="text-sm text-blue-600 hover:text-blue-800"
            >
              Contact Us
            </a>
          </div>
          {/* Right side remains empty for the chat icon */}
          <div className="flex-1"></div>
        </div>
      </div>
    </footer>
  );
}
