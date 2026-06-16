"use client";

import { Suspense } from "react";
import EvidencePageContent from "./EvidencePageContent";

export default function EvidencePage() {
  return (
    <Suspense fallback={<div>Loading evidence...</div>}>
      <EvidencePageContent />
    </Suspense>
  );
}
