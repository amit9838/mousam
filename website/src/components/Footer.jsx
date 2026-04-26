export default function Footer() {
    return (
      <section className="bg-black/80 text-neutral-400 h-24 flex items-center md:px-24 px-8 justify-between border-t border-white/5 font-['Inter']">
        <p className="text-sm">© 2026 Mousam App. All rights reserved.</p>
        <div className="flex gap-6">
           <a href="https://github.com/amit9838/mousam" target="_blank" className="hover:text-white transition-colors">
             <i className="fa-brands fa-github text-2xl"></i>
           </a>
        </div>
      </section>
    );
  }
  