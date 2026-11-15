# Dispatch Log

## 2026-10-02T17:12:29Z

You are the SWE Light orchestrator for Phase 11 (Marks Aggregate & Grading) of the PTMS frontend.

Your working directory is:
`c:\Users\USERAS\Desktop\Defense Frontend\defense-frontend\.agents\teamwork\swe_phase11_1`

The verbatim user request is recorded in:
`c:\Users\USERAS\Desktop\Defense Frontend\defense-frontend\ORIGINAL_REQUEST.md`

## Mission & Requirements:
Implement Phase 11 (Marks Aggregate & Grading) of the Project/Thesis Management System (PTMS) frontend. The frontend is built with React, Vite, TypeScript, Tailwind CSS, and shadcn/ui. This is a single self-contained feature; keep it small and focused.

Working directory of project: `c:\Users\USERAS\Desktop\Defense Frontend\defense-frontend`
Integrity mode: development

### R1. Grading API Service
Implement `src/types/grading.ts` defining the response schema for `GET /v1/batches/{batchId}/marks` (as documented in `docs/BACKEND.md` Phase 12):
- Paginated response (using standard `PaginationMeta` and standard `meta` / `stats` object if applicable).
- Items containing: `studentId`, `roll`, `name`, `supervisorInitial`, `reportReview` (number | null), `finalDefense` (number | null), `external` (number | null), `supervisorMark` (number | null), and `computedGrade` (string | null).
Implement `src/features/grading/api/grading.service.ts` connecting to `GET /v1/batches/{batchId}/marks` endpoint using `apiClient`.
Implement React Query hook `use-marks-aggregate.ts` in `src/features/grading/api/use-marks-aggregate.ts`.

### R2. Admin Marks Sheet UI
Build `AdminMarksSheetTab` in `src/features/grading/admin/components/admin-marks-sheet-tab.tsx`:
- Display a data table (using TanStack Table or a standard HTML table styled with Tailwind) that shows the consolidated marks sheet.
- Include columns for Roll, Name, Supervisor Initial, Report Review (out of 60), Final Defense (out of 20), External (out of 100), Supervisor (out of 100), and Computed Grade.
- Support pagination. (Optionally support search by roll/name if the backend endpoint supports it).

### R3. Tab Integration
Inject the `AdminMarksSheetTab` into the `AdminBatchDetailsPage` component (`src/features/batches/admin/admin-batch-details-page.tsx`) as the "Grading" tab (or "Marks Sheet").
Update the phase status in `docs/PHASES.md` from "Not started" to "Completed".

### Acceptance Criteria
1. API calls are prefixed with `/v1/batches/{batchId}/marks`.
2. The UI maps the backend fields correctly to the table columns.
3. The `AdminMarksSheetTab` renders correctly within the batch details page.
4. The table successfully displays the aggregated marks and computed grade.
5. Type checks (`$env:CI="true"; npx tsc --noEmit` on PowerShell) pass without errors.
6. Existing tests and any new tests pass (`pnpm test` or `npx vitest run`).

Execute the SWE Light loop (implementer, reviewer rounds, test verification). When complete, produce `handoff.md` in your working directory and notify the parent via `send_message`.
