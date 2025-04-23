// angular import
import { Component, inject, OnInit } from '@angular/core';

// bootstrap import
import { NgbDropdownConfig } from '@ng-bootstrap/ng-bootstrap';

// project import
import { SharedModule } from 'src/app/theme/shared/shared.module';

@Component({
  selector: 'app-nav-right',
  imports: [SharedModule],
  templateUrl: './nav-right.component.html',
  styleUrls: ['./nav-right.component.scss'],
  providers: [NgbDropdownConfig]
})
export class NavRightComponent implements OnInit {
  userRole: string = '';
  username: string = '';

  // constructor
  constructor() {
    const config = inject(NgbDropdownConfig);

    config.placement = 'bottom-right';
   
  }
  ngOnInit() {
    this.username = localStorage.getItem('username') || '';
    console.log("Rôle de l'utilisateur:", this.userRole); // ✅ Vérifie si le rôle s'affiche dans la console
  }
  logout() {
    console.log("Déconnexion en cours..."); // ✅ Vérifier si ça s'affiche dans la console
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("user_role");
    window.location.href = "/auth/login";
  }
  
  
}
