import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ListeCarriereComponent } from './liste-carriere.component';

describe('ListeCarriereComponent', () => {
  let component: ListeCarriereComponent;
  let fixture: ComponentFixture<ListeCarriereComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ListeCarriereComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(ListeCarriereComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
