import { CommonModule } from '@angular/common';
import { Component, AfterViewInit, OnInit } from '@angular/core';
import { RouterModule } from '@angular/router';

declare var AOS: any;

@Component({
  selector: 'app-accueil',
  imports:[RouterModule],
  templateUrl: './accueil.component.html',
  styleUrls: ['./accueil.component.scss']
})
export class AccueilComponent implements AfterViewInit, OnInit {
ngAfterViewInit(): void {
  setTimeout(() => {
    AOS.init({
      once: true,      // animations ne se répètent pas
      delay: 100,      // délai d’init
      duration: 600,   // durée de transition
    });
  }, 100); // ← laisse Angular finir de rendre la vue
}


  ngOnInit(): void {
 
  }
}
