import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { EmployeService } from 'src/app/services/employe/employe.service';

type NoteKey =
  | 'technique' | 'communication' | 'performance' | 'travail_d_equipe' | 'leadership'
  | 'qualite' | 'respect_delais' | 'autonomie' | 'initiative' | 'orientation_client'
  | 'assiduite' | 'gestion_stress' | 'securite_conformite' | 'apprentissage' | 'fiabilite';

interface ObjectifPlan {
  libelle: string;
  delai?: string | null;                // ex. '2025-12-31'
  evaluation_fin_cycle?: string | null; // rempli en fin de cycle
}

interface SuiviCarriere {
  id: number;
  ancien_poste?: string | null;
  nouveau_poste: string;
  date_changement: string;    // 'YYYY-MM-DD'
  est_promotion: boolean;
  commentaire?: string | null;
  notes?: Partial<Record<NoteKey, number>>;
  objectifs_plan: ObjectifPlan[]; // <-- on force toujours un tableau
}

@Component({
  selector: 'app-suivi-carriere',
  imports: [CommonModule],
  standalone: true,
  templateUrl: './suivi-carriere.component.html',
  styleUrls: ['./suivi-carriere.component.scss'] 
})
export class SuiviCarriereComponent implements OnInit {
  employeId!: number;
  expandedObjectiveLists = new Set<number>();

  suivis: SuiviCarriere[] = [];
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

  NOTE_LABELS: Record<string, string> = {
    technique: 'Technique',
    communication: 'Communication',
    performance: 'Performance',
    travail_d_equipe: "Travail d'équipe",
    leadership: 'Leadership',
    qualite: 'Qualité',
    respect_delais: 'Respect des délais',
    autonomie: 'Autonomie',
    initiative: 'Initiative / Innovation',
    orientation_client: 'Orientation client',
    assiduite: 'Assiduité',
    gestion_stress: 'Gestion du stress',
    securite_conformite: 'Sécurité & conformité',
    apprentissage: 'Apprentissage',
    fiabilite: 'Fiabilité'
  };

  constructor(
    private route: ActivatedRoute,
    private employeService: EmployeService
  ) {}

  ngOnInit() {
    const employeId = this.route.snapshot.paramMap.get('id');
    if (!employeId) return;

    this.employeId = Number(employeId);

    this.employeService.getSuivis(this.employeId).subscribe((data: any) => {
      // L’API renvoie: { profil, suivi_carriere }
      const profil = data?.profil ?? data?.employe ?? {};
      const rows: any[] = data?.suivi_carriere ?? [];

      // normaliser chaque suivi pour garantir objectifs_plan = []
      this.suivis = rows
        .map((s) => ({
          ...s,
          objectifs_plan: Array.isArray(s.objectifs_plan) ? s.objectifs_plan : []
        }))
        // (optionnel) trier par date la plus récente d’abord
        .sort((a, b) => this.toDate(b.date_changement) - this.toDate(a.date_changement));

      this.employeNom = `${profil?.user?.first_name ?? ''} ${profil?.user?.last_name ?? ''}`.trim();
      this.posteActuel = profil?.poste_actuel ?? '';
      this.departement = profil?.departement ?? '';
      this.dateEmbauche = profil?.date_embauche ?? '';

      this.calculerKPIs();
    });
  }

  private toDate(d: string): number {
    const t = new Date(d).getTime();
    return isNaN(t) ? 0 : t;
  }

  private calculerKPIs() {
    // Ancienneté
    const emb = this.toDate(this.dateEmbauche);
    if (emb) {
      const diffYears = (Date.now() - emb) / (1000 * 60 * 60 * 24 * 365.25);
      this.kpi.anciennete = `${diffYears.toFixed(1)} ans`;
    } else {
      this.kpi.anciennete = '—';
    }

    // Total changements
    this.kpi.totalChangements = this.suivis.length;

    // Total promotions
    this.kpi.totalPromotions = this.suivis.filter(s => !!s.est_promotion).length;

    // Durée moyenne entre changements
    if (this.suivis.length >= 2) {
      const dates = this.suivis
        .map(s => this.toDate(s.date_changement))
        .filter(n => n > 0)
        .sort((a, b) => a - b);

      if (dates.length >= 2) {
        let totalDiff = 0;
        for (let i = 1; i < dates.length; i++) totalDiff += (dates[i] - dates[i - 1]);
        const moyenneMs = totalDiff / (dates.length - 1);
        const moyenneMois = moyenneMs / (1000 * 60 * 60 * 24 * 30.44);
        this.kpi.dureeMoyenneChangement = `${moyenneMois.toFixed(1)} mois`;
        return;
      }
    }
    this.kpi.dureeMoyenneChangement = '—';
  }


  getStars(score: number | null | undefined): ('full' | 'half' | 'empty')[] {
  const types: Array<'full' | 'half' | 'empty'> = [];
  const outOfTen = typeof score === 'number' ? score : 0;
  // Passage sur 5
  const outOfFive = Math.max(0, Math.min(5, outOfTen / 2));
  // Arrondi au 0.5 le plus proche
  const rounded = Math.round(outOfFive * 2) / 2;

  const full = Math.floor(rounded);
  const half = rounded - full === 0.5 ? 1 : 0;
  const empty = 5 - full - half;

  for (let i = 0; i < full; i++) types.push('full');
  if (half) types.push('half');
  for (let i = 0; i < empty; i++) types.push('empty');

  return types;
}
fmtDate(d?: string | null) {
  if (!d) return '—';
  const t = new Date(d);
  return isNaN(t.getTime()) ? d : t.toLocaleDateString(undefined, { day:'2-digit', month:'long', year:'numeric' });
}
showAllObjectives(s: SuiviCarriere): boolean {
  return this.expandedObjectiveLists.has(s.id);
}
toggleObjectivesList(s: SuiviCarriere) {
  this.showAllObjectives(s)
    ? this.expandedObjectiveLists.delete(s.id)
    : this.expandedObjectiveLists.add(s.id);
}
visibleObjectives(s: SuiviCarriere) {
  const list = s.objectifs_plan || [];
  return this.showAllObjectives(s) ? list : list.slice(0, 3);
}
hasHiddenObjectives(s: SuiviCarriere) {
  return (s.objectifs_plan?.length || 0) > 3;
}
}
