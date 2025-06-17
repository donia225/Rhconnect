import { Component, OnInit } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { CommonModule } from '@angular/common';
import { EmployeService } from 'src/app/services/employe/employe.service';
import { Router } from '@angular/router';
import { SidebarComponent } from '../../admin/sidebar/sidebar.component';
import { NavBarComponent } from '../../admin/nav-bar/nav-bar.component';

@Component({
  selector: 'app-employe-profil',
  imports: [CommonModule],
  templateUrl: './employe-profil.component.html',
  styleUrl: './employe-profil.component.scss'
})
export class EmployeProfilComponent  {
  profil: any = {};
  suivi: any[] = [];
  dropdownOpen = false;

  constructor(private http: HttpClient, private employeService: EmployeService, private router: Router) {}
/* 
  toggleDropdown() {
  this.dropdownOpen = !this.dropdownOpen;
}
   ngOnInit() {
    this.employeService.getEmployeProfilEtSuivi().subscribe(data => {
      this.profil = data.profil;
      this.suivi = data.suivi_carriere;
    });
  }

  logout() {
  localStorage.clear();
  this.router.navigate(['/auth/login']);
} */

}
