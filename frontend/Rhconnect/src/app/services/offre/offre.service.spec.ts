import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';

import { OffreService } from './offre.service';

describe('OffreService', () => {
  let service: OffreService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        OffreService,
        provideHttpClient(),
        provideHttpClientTesting()
      ]
    });

    service = TestBed.inject(OffreService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});