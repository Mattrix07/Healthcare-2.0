import type { PriorAuthRequest } from "./types";

export const SAMPLE_REQUEST: PriorAuthRequest = {
  patient_name: "Sarah Nguyen",
  patient_dob: "1967-08-24",
  provider_npi: "AHPRA-MED0001234567",
  diagnosis_codes: ["M17.11", "M25.56"],
  procedure_codes: ["49518", "48915"],
  clinical_notes:
    "58-year-old member with severe right knee osteoarthritis referred by an orthopaedic surgeon for elective total knee replacement at a contracted private hospital in Brisbane. Symptoms have progressed over 18 months with daily pain, night pain, reduced walking tolerance to less than 200 metres, difficulty climbing stairs and loss of capacity to complete usual work and home activities.\n\n" +
    "Conservative management has been trialled and documented, including supervised physiotherapy for 12 weeks, NSAID and paracetamol therapy, weight-management advice, activity modification and intra-articular corticosteroid injection with only transient relief. The member reports persistent functional impairment despite these measures.\n\n" +
    "Imaging: weight-bearing X-ray and MRI show advanced medial compartment osteoarthritis with near complete joint-space loss, osteophytes, subchondral sclerosis and degenerative meniscal tearing. Orthopaedic assessment confirms that non-operative options are exhausted and recommends right total knee arthroplasty.\n\n" +
    "Private health context: hospital admission is planned as an elective inpatient episode. Reviewer should confirm active hospital cover, waiting periods, pre-existing condition status, hospital agreement status, MBS item alignment, prosthesis/device benefit considerations, excess/co-payment settings and any gap scheme participation before issuing a funding position.",
  insurance_id: "BUPA-AU-7429135",
};
