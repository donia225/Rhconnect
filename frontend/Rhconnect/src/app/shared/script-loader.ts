export class ScriptLoader {
  private static loaded = new Set<string>();

  static load(src: string): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.loaded.has(src)) return resolve();
      const s = document.createElement('script');
      s.src = src;
      s.defer = true;
      s.onload = () => { this.loaded.add(src); resolve(); };
      s.onerror = (e) => reject(e);
      document.body.appendChild(s);
    });
  }
}
