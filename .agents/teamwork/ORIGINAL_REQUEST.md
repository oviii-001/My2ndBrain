# Original User Request

## 2026-10-02T15:45:02Z

Implement Phase 10 (Email - Admin Only) of the Project/Thesis Management System (PTMS) frontend. The frontend is built with React, Next.js (Vite), TypeScript, Tailwind CSS, and shadcn/ui. This is a single self-contained feature; keep it small and focused.

Working directory: c:\Users\USERAS\Desktop\Defense Frontend\defense-frontend
Integrity mode: development

## Requirements

### R1. Email Service and API Types
Implement `src/types/email.ts` representing the five email request/response payloads (`BoardAssignmentsEmailRequest`, `DefenseDatesEmailRequest`, etc.) according to `docs/api/openapi.yaml`. Implement `src/features/email/api/email.service.ts` connecting to the 5 email endpoints using `apiClient`. Implement React Query mutations in `use-email.ts` for these 5 actions.

### R2. Admin Email Tab UI
Create an `AdminEmailTab` component in `src/features/email/admin/components/admin-email-tab.tsx` that exposes UI controls (e.g. buttons/cards) to trigger the 5 email endpoints. Allow the admin to optionally provide filters (e.g., `boardType`, `defenseType`, `facultyId`) before sending, or just provide simple Send buttons that confirm the action. Use the project's existing `useToast` to report successes and errors. 

### R3. Tab Integration
Inject the `AdminEmailTab` into the `AdminBatchDetailsPage` component (`src/features/batches/admin/admin-batch-details-page.tsx`) as the "Emails" tab. Update the phase status in `docs/PHASES.md` from "Not started" to "Completed".

## Acceptance Criteria

### API Compliance
- [ ] All request payloads match `openapi.yaml`.
- [ ] API calls are prefixed with `/v1/batches/{batchId}/email/`.

### Functionality
- [ ] The `AdminEmailTab` renders correctly within the batch details page.
- [ ] 5 distinct actions are available (Board Assignments, Mid Dates, Final Dates, Supervisor Feedback, Absent List).
- [ ] Type checks (`npx tsc --noEmit` but with `$env:CI="true";` prefix on powershell) pass without errors for the new feature.

## 2026-10-02T15:45:08Z

The user wants this to be completed automatically. Please proceed to implement the feature and verify it without asking the user for input unless you are absolutely blocked. When done, reply back with the success criteria.

## 2026-10-02T17:11:04Z

Implement Phase 11 (Marks Aggregate & Grading) of the Project/Thesis Management System (PTMS) frontend. The frontend is built with React, Next.js (Vite), TypeScript, Tailwind CSS, and shadcn/ui. This is a single self-contained feature; keep it small and focused.

Working directory: c:\Users\USERAS\Desktop\Defense Frontend\defense-frontend
Integrity mode: development

## Requirements

### R1. Grading API Service
Implement `src/features/grading/api/grading.service.ts` connecting to the `GET /v1/batches/{batchId}/marks` endpoint (as documented in `docs/BACKEND.md` Phase 12). 
Since this endpoint is missing from `openapi.yaml`, define the response schema in `src/types/grading.ts`:
- Paginated response (using standard `PaginationMeta` and standard `meta` / `stats` object if applicable).
- Items containing: `studentId`, `roll`, `name`, `supervisorInitial`, `reportReview` (number | null), `finalDefense` (number | null), `external` (number | null), `supervisorMark` (number | null), and `computedGrade` (string | null).
Implement React Query hook `use-marks-aggregate.ts` in `src/features/grading/api/use-marks-aggregate.ts`.

### R2. Admin Marks Sheet UI
Build `AdminMarksSheetTab` in `src/features/grading/admin/components/admin-marks-sheet-tab.tsx`.
- Display a data table (using TanStack Table or a standard HTML table styled with Tailwind) that shows the consolidated marks sheet.
- Include columns for Roll, Name, Supervisor Initial, Report Review (out of 60), Final Defense (out of 20), External (out of 100), Supervisor (out of 100), and Computed Grade.
- Support pagination. (Optionally support search by roll/name if the backend endpoint supports it).

### R3. Tab Integration
Inject the `AdminMarksSheetTab` into the `AdminBatchDetailsPage` component (`src/features/batches/admin/admin-batch-details-page.tsx`) as the "Grading" tab (or "Marks Sheet").
Update the phase status in `docs/PHASES.md` from "Not started" to "Completed".

## Acceptance Criteria

### API Compliance
- [ ] API calls are prefixed with `/v1/batches/{batchId}/marks`.
- [ ] The UI maps the backend fields correctly to the table columns.

### Functionality
- [ ] The `AdminMarksSheetTab` renders correctly within the batch details page.
- [ ] The table successfully displays the aggregated marks and computed grade.
- [ ] Type checks (`npx tsc --noEmit` but with `$env:CI="true";` prefix on powershell) pass without errors for the new feature.

## 2026-10-02T17:11:10Z

The user wants this to be completed automatically. Please proceed to implement the feature and verify it without asking the user for input unless you are absolutely blocked. When done, reply back with the success criteria.
