import { CommonModule } from '@angular/common';
import { Component, HostListener, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { EmployeService } from 'src/app/services/employe/employe.service';

@Component({
  selector: 'app-navbar-employe',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './navbar-employe.component.html',
  styleUrls: ['./navbar-employe.component.scss']
})
export class NavbarEmployeComponent implements OnInit {
  fullName = '';
  avatarUrl = '';
  dropdownOpen = false;

  constructor(private router: Router, private employeService: EmployeService) {}

  ngOnInit() {
    const toUrl = (u?: string) => (u ? (u.startsWith('http') ? u : `http://127.0.0.1:8000${u}`) : '');

    this.employeService.getMonProfilEtSuivi().subscribe({
      next: (data: any) => {
        const profil = data?.profil ?? {};
        this.fullName = `${profil.prenom || ''} ${profil.nom || ''}`.trim();
        this.avatarUrl = profil.avatar ? toUrl(profil.avatar) : '';
      },
      error: (e) => console.error('Erreur chargement profil', e)
    });

    this.employeService.avatarChanged$.subscribe((url) => {
      if (url) this.avatarUrl = url;
    });
  }

  toggleDropdown(event: Event) {
    event.preventDefault();
    this.dropdownOpen = !this.dropdownOpen;
  }

  @HostListener('document:keydown.escape')
  onEsc() {
    this.dropdownOpen = false;
  }

  @HostListener('document:click', ['$event'])
  onDocClick(event: MouseEvent) {
    const target = event.target as HTMLElement;
    if (!target.closest('.user-menu')) this.dropdownOpen = false;
  }

  logout() {
    localStorage.clear();
    this.router.navigate(['/auth/login']);
  }
}
