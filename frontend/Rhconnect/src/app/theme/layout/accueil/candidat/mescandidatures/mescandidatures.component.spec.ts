import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';

import { MescandidaturesComponent } from './mescandidatures.component';

describe('MescandidaturesComponent', () => {
  let component: MescandidaturesComponent;
  let fixture: ComponentFixture<MescandidaturesComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [MescandidaturesComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting()
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(MescandidaturesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});