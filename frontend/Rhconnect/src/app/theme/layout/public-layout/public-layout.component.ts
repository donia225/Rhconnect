import { Component } from '@angular/core';
import { NavbarComponent } from "../accueil/navbar/navbar.component";
import { RouterModule } from '@angular/router';

@Component({
  selector: 'app-public-layout',
  imports: [NavbarComponent, RouterModule],
  templateUrl: './public-layout.component.html',
  styleUrl: './public-layout.component.scss'
})
export class PublicLayoutComponent {

}
