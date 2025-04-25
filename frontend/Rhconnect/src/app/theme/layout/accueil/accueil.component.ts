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
    AOS.init();
  }

  ngOnInit(): void {
 
  }
}
