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
   const script = document.createElement('script');
  script.src = 'assets/js/main.js';
  script.async = true;
  document.body.appendChild(script);
  setTimeout(() => {
    AOS.init({
      once: true,      
      delay: 100,      
      duration: 600, 
    });
  }, 100);
}


  ngOnInit(): void {
 
  }
}
