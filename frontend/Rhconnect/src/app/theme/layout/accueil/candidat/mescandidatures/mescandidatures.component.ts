import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';

import { OffreService } from 'src/app/services/offre/offre.service';

@Component({
  selector: 'app-mescandidatures',
  imports:[CommonModule],
  templateUrl: './mescandidatures.component.html',
  styleUrls: ['./mescandidatures.component.scss']
})
export class MescandidaturesComponent implements OnInit {
  candidatures: any[] = [];
  loading = true;

  constructor(private offreService: OffreService) {}

  ngOnInit(): void {
    this.offreService.getMesCandidatures().subscribe({
      next: (data) => {
        this.candidatures = data;
        this.loading = false;
      },
      error: (err) => {
        this.loading = false;
        alert('Erreur lors du chargement des candidatures');
      }
    });
  }
}
