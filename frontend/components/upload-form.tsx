"use client";

import { useRef, useState } from "react";
import { toast } from "sonner";
import { Loader2, Plus, X, FlaskConical, User, CalendarDays, Hash, CreditCard, Stethoscope, FileText, Send } from "lucide-react";
import type { PriorAuthRequest, ReviewResponse, ReviewProgress, ProgressEvent, AgentId } from "@/lib/types";
import { submitReviewStream } from "@/lib/api";
import { SAMPLE_REQUEST } from "@/lib/sample-case";
import { ProgressTracker } from "@/components/progress-tracker";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Alert, AlertDescription } from "@/components/ui/alert";

interface UploadFormProps {
  onReviewComplete: (review: ReviewResponse) => void;
}

const emptyRequest: PriorAuthRequest = {
  patient_name: "",
  patient_dob: "",
  provider_npi: "",
  diagnosis_codes: [""],
  procedure_codes: [""],
  clinical_notes: "",
  insurance_id: "",
};

export function UploadForm({ onReviewComplete }: UploadFormProps) {
  const [form, setForm] = useState<PriorAuthRequest>(emptyRequest);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState<ReviewProgress | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const initialProgress: ReviewProgress = {
    currentPhase: "preflight",
    progressPct: 0,
    message: "Starting AU private health funding review...",
    agents: {
      compliance: { status: "pending", detail: "Waiting" },
      clinical: { status: "pending", detail: "Waiting" },
      coverage: { status: "pending", detail: "Waiting" },
      synthesis: { status: "pending", detail: "Waiting" },
    },
    phases: {
      preflight: "pending",
      phase_1: "pending",
      phase_2: "pending",
      phase_3: "pending",
      phase_4: "pending",
    },
  };

  function applyProgressEvent(prev: ReviewProgress, event: ProgressEvent): ReviewProgress {
    const next = { ...prev };
    next.currentPhase = event.phase;
    next.progressPct = event.progress_pct;
    next.message = event.message;
    next.phases = { ...prev.phases, [event.phase]: event.status };
    next.agents = { ...prev.agents };
    for (const [agentId, agentState] of Object.entries(event.agents ?? {})) {
      next.agents[agentId as AgentId] = agentState;
    }
    return next;
  }

  function updateField<K extends keyof PriorAuthRequest>(
    key: K,
    value: PriorAuthRequest[K]
  ) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  function updateCode(
    field: "diagnosis_codes" | "procedure_codes",
    index: number,
    value: string
  ) {
    const updated = [...form[field]];
    updated[index] = value;
    updateField(field, updated);
  }

  function addCode(field: "diagnosis_codes" | "procedure_codes") {
    updateField(field, [...form[field], ""]);
  }

  function removeCode(
    field: "diagnosis_codes" | "procedure_codes",
    index: number
  ) {
    if (form[field].length <= 1) return;
    updateField(
      field,
      form[field].filter((_, i) => i !== index)
    );
  }

  function loadSample() {
    setForm({ ...SAMPLE_REQUEST });
    setError(null);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    const cleaned: PriorAuthRequest = {
      ...form,
      diagnosis_codes: form.diagnosis_codes
        .map((c) => c.trim().toUpperCase())
        .filter((c) => c),
      procedure_codes: form.procedure_codes
        .map((c) => c.trim().toUpperCase())
        .filter((c) => c),
    };

    if (cleaned.diagnosis_codes.length === 0) {
      setError("Add at least one diagnosis code, usually ICD-10-AM or ICD-10 format.");
      return;
    }
    if (cleaned.procedure_codes.length === 0) {
      setError("Add at least one MBS item number or procedure code.");
      return;
    }
    if (cleaned.patient_dob && cleaned.patient_dob > new Date().toISOString().slice(0, 10)) {
      setError("Date of birth cannot be in the future.");
      return;
    }

    setLoading(true);
    setProgress(initialProgress);

    abortRef.current = submitReviewStream(
      cleaned,
      (event) => {
        setProgress((prev) => prev ? applyProgressEvent(prev, event) : prev);
      },
      (result) => {
        setLoading(false);
        setProgress(null);
        onReviewComplete(result);
        toast.success("Funding review complete", {
          description: result.recommendation === "approve"
            ? "Draft position: Eligible to fund"
            : "Draft position: Pend for human review",
        });
      },
      (errMsg) => {
        setLoading(false);
        setProgress((prev) => prev ? { ...prev, error: errMsg } : prev);
        setError(errMsg);
        toast.error("Review failed", { description: errMsg });
      },
    );
  }

  return (
    <Card className="shadow-sm">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <div>
          <CardTitle className="text-lg flex items-center gap-2">
            <FileText className="h-5 w-5 text-primary" />
            New Pre-admission Funding Request
          </CardTitle>
          <p className="text-sm text-muted-foreground mt-1">
            Enter member, provider, item and clinical details for an AI-assisted Australian private health insurance review
          </p>
        </div>
        <Button variant="secondary" size="sm" onClick={loadSample}>
          <FlaskConical className="mr-1 h-3.5 w-3.5" />
          Load AU Sample Case
        </Button>
      </CardHeader>

      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="patient_name" className="flex items-center gap-1.5">
                <User className="h-3.5 w-3.5 text-muted-foreground" />
                Member Name
              </Label>
              <Input
                id="patient_name"
                placeholder="Sarah Nguyen"
                value={form.patient_name}
                onChange={(e) => updateField("patient_name", e.target.value)}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="patient_dob" className="flex items-center gap-1.5">
                <CalendarDays className="h-3.5 w-3.5 text-muted-foreground" />
                Date of Birth
              </Label>
              <Input
                id="patient_dob"
                type="date"
                value={form.patient_dob}
                max={new Date().toISOString().slice(0, 10)}
                onChange={(e) => updateField("patient_dob", e.target.value)}
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="provider_npi" className="flex items-center gap-1.5">
                <Hash className="h-3.5 w-3.5 text-muted-foreground" />
                Provider Identifier
              </Label>
              <Input
                id="provider_npi"
                placeholder="AHPRA-MED0001234567 or provider number"
                value={form.provider_npi}
                onChange={(e) => updateField("provider_npi", e.target.value)}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="insurance_id" className="flex items-center gap-1.5">
                <CreditCard className="h-3.5 w-3.5 text-muted-foreground" />
                Member / Policy Number
              </Label>
              <Input
                id="insurance_id"
                placeholder="BUPA-AU-7429135"
                value={form.insurance_id ?? ""}
                onChange={(e) => updateField("insurance_id", e.target.value)}
              />
            </div>
          </div>

          <div className="relative">
            <div className="absolute inset-0 flex items-center"><span className="w-full border-t" /></div>
            <div className="relative flex justify-center text-xs uppercase"><span className="bg-card px-2 text-muted-foreground">Codes and item numbers</span></div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label className="flex items-center gap-1.5">
                <Stethoscope className="h-3.5 w-3.5 text-muted-foreground" />
                Diagnosis Codes
              </Label>
              {form.diagnosis_codes.map((code, i) => (
                <div key={i} className="flex gap-1">
                  <Input
                    placeholder="e.g. M17.11"
                    value={code}
                    pattern="^[A-Ta-tV-Zv-z][0-9][A-Za-z0-9](?:\.[A-Za-z0-9]{1,4})?$"
                    title="ICD-10 / ICD-10-AM style format, e.g. M17.11, J18.9"
                    required={i === 0}
                    onChange={(e) =>
                      updateCode("diagnosis_codes", i, e.target.value)
                    }
                  />
                  {form.diagnosis_codes.length > 1 && (
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      onClick={() => removeCode("diagnosis_codes", i)}
                    >
                      <X className="h-3.5 w-3.5" />
                    </Button>
                  )}
                </div>
              ))}
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => addCode("diagnosis_codes")}
              >
                <Plus className="mr-1 h-3.5 w-3.5" />
                Add Code
              </Button>
            </div>

            <div className="space-y-2">
              <Label className="flex items-center gap-1.5">
                <Hash className="h-3.5 w-3.5 text-muted-foreground" />
                MBS / Procedure Item Numbers
              </Label>
              {form.procedure_codes.map((code, i) => (
                <div key={i} className="flex gap-1">
                  <Input
                    placeholder="e.g. 49518"
                    value={code}
                    pattern="^([0-9]{4,6}[0-9A-Za-z]?|[A-Za-z][0-9]{4,6})$"
                    title="MBS item or procedure code, e.g. 49518, 48915, 18213"
                    required={i === 0}
                    onChange={(e) =>
                      updateCode("procedure_codes", i, e.target.value)
                    }
                  />
                  {form.procedure_codes.length > 1 && (
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      onClick={() => removeCode("procedure_codes", i)}
                    >
                      <X className="h-3.5 w-3.5" />
                    </Button>
                  )}
                </div>
              ))}
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => addCode("procedure_codes")}
              >
                <Plus className="mr-1 h-3.5 w-3.5" />
                Add Item
              </Button>
            </div>
          </div>

          <div className="relative">
            <div className="absolute inset-0 flex items-center"><span className="w-full border-t" /></div>
            <div className="relative flex justify-center text-xs uppercase"><span className="bg-card px-2 text-muted-foreground">Clinical and funding context</span></div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="clinical_notes" className="flex items-center gap-1.5">
              <FileText className="h-3.5 w-3.5 text-muted-foreground" />
              Clinical Notes and Admission Context
            </Label>
            <Textarea
              id="clinical_notes"
              rows={6}
              placeholder="Enter clinical notes, planned admission, hospital, prior conservative treatment, diagnostics, item numbers, prosthesis/device considerations and insurer policy context..."
              value={form.clinical_notes}
              onChange={(e) => updateField("clinical_notes", e.target.value)}
              required
            />
          </div>

          {progress && (
            <ProgressTracker progress={progress} />
          )}

          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <Button type="submit" className="w-full bg-gradient-to-r from-brand to-brand-dark hover:from-brand-hover hover:to-brand-hover-dark text-white shadow-md" disabled={loading}>
            {loading ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Send className="mr-2 h-4 w-4" />
            )}
            {loading ? "Submitting funding review..." : "Submit for Funding Review"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
