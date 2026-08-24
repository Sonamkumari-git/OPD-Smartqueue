# Nurse and Doctor Vital Collaboration

Every workflow observation is persisted in MongoDB with its `patient_id`, `patient_name`, `token_id`, recording nurse, and timestamps. Nurses can edit or delete only observations they recorded, and only while the linked visit remains active in one of their assigned departments.

The assigned doctor can retrieve the same patient-linked vital history only while the patient has an active consultation with that doctor. The Nurse Dashboard now presents the patient name on each history item alongside edit and delete controls when the observation belongs to the signed-in nurse.

The deployed Atlas workflow was verified end to end: a nurse created and edited an observation for `C-001 · Vikram Patel`; the assigned doctor started the consultation and retrieved the updated observation; the nurse then deleted it and the record was absent from history.
