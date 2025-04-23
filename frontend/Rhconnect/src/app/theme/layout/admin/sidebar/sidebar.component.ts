import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { RouterModule } from '@angular/router';
import { NavLogoComponent } from '../navigation/nav-logo/nav-logo.component';

@Component({
  selector: 'app-sidebar',
  imports: [RouterModule, CommonModule, NavLogoComponent],
  templateUrl: './sidebar.component.html',
  styleUrl: './sidebar.component.scss'
})
export class SidebarComponent {
  userRole: string | null = localStorage.getItem('user_role'); // Get role from storage
  dropdownStates = {
    offres: false,
    carriere: false
  };
  toggleDropdown(menu: 'offres' | 'carriere') {
    this.dropdownStates[menu] = !this.dropdownStates[menu];
  }


  constructor() {}

  isGestionnaireRH(): boolean {
    return this.userRole === 'gestionnaire_rh';
  }

  isRecruteur(): boolean {
    return this.userRole === 'recruteur';
  }

  
}
