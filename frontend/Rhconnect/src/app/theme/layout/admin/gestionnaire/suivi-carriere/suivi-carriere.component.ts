import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { EmployeService } from 'src/app/services/employe/employe.service';

@Component({
  selector: 'app-suivi-carriere',
  imports: [CommonModule],
  templateUrl: './suivi-carriere.component.html',
})
export class SuiviCarriereComponent implements OnInit {
  employeId!: number;
  suivis: any[] = [];
  employeNom = '';
  posteActuel = '';
  departement = '';
  dateEmbauche!: string;

  kpi = {
    totalChangements: 0,
    totalPromotions: 0,
    anciennete: '',
    dureeMoyenneChangement: ''
  };
  NOTE_LABELS: Record<string,string> = {
    technique: 'Technique', communication: 'Communication', performance: 'Performance',
    travail_d_equipe: "Travail d'équipe", leadership: 'Leadership',
    qualite: 'Qualité', respect_delais: 'Respect des délais',
    autonomie: 'Autonomie', initiative: 'Initiative / Innovation',
    orientation_client: 'Orientation client', assiduite: 'Assiduité',
    gestion_stress: 'Gestion du stress', securite_conformite: 'Sécurité & conformité',
    apprentissage: 'Apprentissage', fiabilite: 'Fiabilité'
  };
  
  constructor(
    private route: ActivatedRoute,
    private employeService: EmployeService
  ) {}

ngOnInit() {
    const employeId = this.route.snapshot.paramMap.get('id');
    if (employeId) {
      this.employeId = Number(employeId);
      this.employeService.getSuivis(this.employeId).subscribe((data) => {
        const profil = data.profil;
        this.suivis = data.suivi_carriere;
        this.employeNom = `${profil.user.first_name} ${profil.user.last_name}`;
        this.posteActuel = profil.poste_actuel;
        this.departement = profil.departement;
        this.dateEmbauche = profil.date_embauche;

        this.calculerKPIs();
      });
    }
  }

  private calculerKPIs() {
    // Ancienneté
    const dateEmbauche = new Date(this.dateEmbauche);
    const aujourdHui = new Date();
    const diffMs = aujourdHui.getTime() - dateEmbauche.getTime();
    const diffYears = diffMs / (1000 * 60 * 60 * 24 * 365.25);
    this.kpi.anciennete = `${diffYears.toFixed(1)} ans`;

    // Total changements de poste
    this.kpi.totalChangements = this.suivis.length;

    // Total promotions
    this.kpi.totalPromotions = this.suivis.filter(s => s.est_promotion).length;

    // Durée moyenne entre changements
    if (this.suivis.length >= 2) {
      const dates = this.suivis
        .map(s => new Date(s.date_changement))
        .sort((a, b) => a.getTime() - b.getTime());

      let totalDiff = 0;
      for (let i = 1; i < dates.length; i++) {
        const diff = dates[i].getTime() - dates[i - 1].getTime();
        totalDiff += diff;
      }

      const moyenneMs = totalDiff / (dates.length - 1);
      const moyenneMois = moyenneMs / (1000 * 60 * 60 * 24 * 30.44);
      this.kpi.dureeMoyenneChangement = `${moyenneMois.toFixed(1)} mois`;
    } else {
      this.kpi.dureeMoyenneChangement = '—';
    }
  }
}