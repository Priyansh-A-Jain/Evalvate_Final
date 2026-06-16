export default function Footer() {
  return (
    <footer className="relative border-t border-white/5 bg-black px-6 md:px-12 py-16">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-start md:items-end justify-between gap-12">
        <div>
          <div className="flex items-center gap-2 mb-6">
            <span className="font-display font-extrabold text-[22px] tracking-tight text-white">evalvate</span>
            <span className="w-1.5 h-1.5 rounded-full bg-orange-500" />
          </div>
          <p className="max-w-xs text-white/40 text-[13px] leading-relaxed">
            A quiet, ruthless interview preparation engine. Built for the moment before the moment.
          </p>
        </div>
        <div className="grid grid-cols-3 gap-12 text-[12px] font-mono tracking-[0.15em] uppercase">
          <div>
            <div className="text-white/30 mb-4">Product</div>
            <ul className="space-y-3 text-white/70">
              <li><a href="#">Mock interviews</a></li>
              <li><a href="#">Speech analysis</a></li>
              <li><a href="#">Resume audit</a></li>
            </ul>
          </div>
          <div>
            <div className="text-white/30 mb-4">Company</div>
            <ul className="space-y-3 text-white/70">
              <li><a href="#">Manifesto</a></li>
              <li><a href="#">Careers</a></li>
              <li><a href="#">Press</a></li>
            </ul>
          </div>
          <div>
            <div className="text-white/30 mb-4">Connect</div>
            <ul className="space-y-3 text-white/70">
              <li><a href="#">Twitter</a></li>
              <li><a href="#">LinkedIn</a></li>
              <li><a href="#">Contact</a></li>
            </ul>
          </div>
        </div>
      </div>
      <div className="max-w-7xl mx-auto mt-16 pt-6 border-t border-white/5 flex flex-col md:flex-row items-center justify-between gap-3 text-[11px] font-mono tracking-[0.2em] uppercase text-white/30">
        <span>© 2025 evalvate - all rights reserved</span>
        <span>built for the twelve minutes that change a career</span>
      </div>
    </footer>
  );
}
