import { ComponentFixture, TestBed } from '@angular/core/testing';

import { SuiviCarriereComponent } from './suivi-carriere.component';

describe('SuiviCarriereComponent', () => {
  let component: SuiviCarriereComponent;
  let fixture: ComponentFixture<SuiviCarriereComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SuiviCarriereComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(SuiviCarriereComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
