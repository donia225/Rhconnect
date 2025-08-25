import { Component, AfterViewInit, inject } from '@angular/core';
import { RouterModule } from '@angular/router';
import { NavbarComponent } from '../accueil/navbar/navbar.component';
import { ScriptLoader } from 'src/app/shared/script-loader';

@Component({
  selector: 'app-public-layout',
  standalone: true,
  imports: [NavbarComponent, RouterModule],
  templateUrl: './public-layout.component.html',
  styleUrl: './public-layout.component.scss'
})
export class PublicLayoutComponent implements AfterViewInit {

  async ngAfterViewInit() {
    // IMPORTANT : l'ordre
    try {
      await ScriptLoader.load('/assets/vendor/aos/aos.js');
      (window as any).AOS?.init?.({ duration: 600, easing: 'ease-in-out', once: true, mirror: false });

      await ScriptLoader.load('/assets/vendor/glightbox/js/glightbox.min.js');
      await ScriptLoader.load('/assets/vendor/purecounter/purecounter_vanilla.js');
      await ScriptLoader.load('/assets/vendor/imagesloaded/imagesloaded.pkgd.min.js');
      await ScriptLoader.load('/assets/vendor/isotope-layout/isotope.pkgd.min.js');
      await ScriptLoader.load('/assets/vendor/swiper/swiper-bundle.min.js');

      // Enfin, ton main.js (version “safe” avec gardes ou celle que je t’ai donnée)
      await ScriptLoader.load('/assets/js/main.js');

    } catch (e) {
      console.error('Erreur chargement scripts public:', e);
    }
  }
}
