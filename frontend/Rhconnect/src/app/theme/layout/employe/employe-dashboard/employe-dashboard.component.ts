import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { RouterModule } from '@angular/router';
import { EmployeService } from 'src/app/services/employe/employe.service';

type Kpi = { id: string; label: string; value: string | number; icon: string; class: string; hint?: string };
type Suivi = {
  ancien_poste?: string | null;
  nouveau_poste: string;
  date_changement?: string | null;
  est_promotion: boolean;
  commentaire?: string | null;
  notes?: Record<string, number>;
  objectifs_plan?: Array<{ libelle: string; delai?: string | null; evaluation_fin_cycle?: string | null }>;
};

@Component({
  selector: 'app-employe-dashboard',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './employe-dashboard.component.html',
  styleUrls: ['./employe-dashboard.component.scss']
})
export class EmployeDashboardComponent implements OnInit {
  loading = true;
  profil: any = null;
  suivis: Suivi[] = [];

  // KPI
  anciennete = '—';
  totalChangements = 0;
  totalPromotions = 0;
  dureeMoyenneChangement = '—';
  kpis: Kpi[] = [];

  // Contenu sous les KPI
  lastMove: Suivi | null = null;
  currentObjectives: Suivi['objectifs_plan'] = [];
  last3: Suivi[] = [];

  constructor(private employeService: EmployeService) {}

  ngOnInit(): void {
    this.employeService.getMonProfilEtSuivi().subscribe({
      next: (data: any) => {
        this.profil = data?.profil ?? data?.employe ?? {};
        this.suivis = (data?.suivi_carriere ?? []).slice();
        this.computeMetrics();
        this.buildKpis();
        this.buildCards();
        this.loading = false;
      },
      error: () => (this.loading = false)
    });
  }

  private computeMetrics() {
    // Ancienneté
    const emb = this.toDate(this.profil?.date_embauche);
    if (emb) {
      const diffYears = (Date.now() - emb) / (1000 * 60 * 60 * 24 * 365.25);
      this.anciennete = `${diffYears.toFixed(1)} ans`;
    }

    // Tri desc
    const desc = this.suivis
      .filter(Boolean)
      .sort((a, b) => new Date(b?.date_changement || 0).getTime() - new Date(a?.date_changement || 0).getTime());

    this.totalChangements = desc.length;
    this.totalPromotions = desc.filter(s => !!s.est_promotion).length;

    // Durée moyenne entre changements
    if (desc.length >= 2) {
      const dates = desc
        .map(s => this.toDate(s.date_changement || ''))
        .filter(n => n > 0)
        .sort((a, b) => a - b);
      if (dates.length >= 2) {
        let sum = 0;
        for (let i = 1; i < dates.length; i++) sum += dates[i] - dates[i - 1];
        const avgMonths = sum / (dates.length - 1) / (1000 * 60 * 60 * 24 * 30.44);
        this.dureeMoyenneChangement = `${avgMonths.toFixed(1)} mois`;
      }
    }

    // Aperçu + mini-timeline
    const descAll = this.suivis
      .slice()
      .sort((a, b) => new Date(b?.date_changement || 0).getTime() - new Date(a?.date_changement || 0).getTime());

    this.lastMove = descAll[0] ?? null;
    this.currentObjectives = this.lastMove?.objectifs_plan?.length ? this.lastMove.objectifs_plan : [];
    this.last3 = descAll.slice(0, 3);
  }

  private buildKpis() {
    this.kpis = [
      {
        id: 'tenure',
        label: 'Ancienneté',
        value: this.anciennete,
        icon: 'bi-hourglass-split',
        class: 'kpi--tenure',
        hint: this.profil?.date_embauche ? `Depuis le ${this.formatDate(this.profil.date_embauche)}` : ''
      },
      {
        id: 'changes',
        label: 'Changements de poste',
        value: this.totalChangements,
        icon: 'bi-arrow-left-right',
        class: 'kpi--changes',
        hint: this.totalChangements ? 'Historique des mouvements' : 'Aucun'
      },
      {
        id: 'promos',
        label: 'Promotions',
        value: this.totalPromotions,
        icon: 'bi-graph-up-arrow',
        class: 'kpi--promos',
        hint: this.totalPromotions ? 'Félicitations !' : '—'
      },
      {
        id: 'avg',
        label: 'Durée moyenne entre changements',
        value: this.dureeMoyenneChangement,
        icon: 'bi-clock-history',
        class: 'kpi--avg',
        hint: this.totalChangements >= 2 ? 'Moyenne calculée' : 'Données insuffisantes'
      }
    ];
  }

  private buildCards() {
    // placeholder si tu enrichis plus tard
  }

  fmtDate(d?: string | null) {
    if (!d) return '—';
    const t = new Date(d);
    if (isNaN(t.getTime())) return d || '—';
    return t.toLocaleDateString(undefined, { day: '2-digit', month: 'long', year: 'numeric' });
  }

  private toDate(d: string | null | undefined): number {
    if (!d) return 0;
    const t = new Date(d).getTime();
    return isNaN(t) ? 0 : t;
  }

  private formatDate(d: string) {
    try {
      const dt = new Date(d);
      return dt.toLocaleDateString(undefined, { day: '2-digit', month: 'long', year: 'numeric' });
    } catch {
      return d;
    }
  }
}
