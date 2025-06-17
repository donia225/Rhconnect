import { CommonModule } from '@angular/common';
import { Component, HostListener, OnInit } from '@angular/core';
import { Router } from '@angular/router';

@Component({
  selector: 'app-navbar-employe',
  imports:[CommonModule],
  templateUrl: './navbar-employe.component.html',
  styleUrls: ['./navbar-employe.component.scss']
})
export class NavbarEmployeComponent implements OnInit {
  userRole: string = '';
  username: string = '';
  dropdownOpen = false;


  constructor(private router: Router) {}

  toggleDropdown(event: Event) {
    event.preventDefault();
    this.dropdownOpen = !this.dropdownOpen;
  }
    @HostListener('document:click', ['$event'])
    onDocClick(event: MouseEvent) {
      const target = event.target as HTMLElement;
      if (!target.closest('.user-menu')) {
        this.dropdownOpen = false;
      }
    }
  logout() {
    localStorage.clear();
    this.router.navigate(['/auth/login']);
  }
  ngOnInit() {
    this.username = localStorage.getItem('username') || '';
    console.log("Rôle de l'utilisateur:", this.userRole); // ✅ Vérifie si le rôle s'affiche dans la console
  }
}
