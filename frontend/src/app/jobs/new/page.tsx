"use client";

import React, { useEffect } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";

import Card from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import Button from "@/components/ui/Button";
import { useAuth } from "@/hooks/useAuth";

// Zod schema per Section 8.3 body
const postJobSchema = z.object({
  title: z.string().min(1, "Title is required"),
  description: z.string().min(1, "Description is required"),
  capabilities: z.array(z.string()).min(1, "Select at least one capability"),
  payment_token: z.string().min(1, "Payment token is required"),
  escrow_amount: z.string().min(1, "Escrow amount is required"),
  deadline: z.string().datetime({ message: "Provide a valid deadline" }),
});

type PostJobValues = z.infer<typeof postJobSchema>;

// GAP resolution: Capability options list is not specified in blueprint.
// Use pragmatic defaults consistent with Register page.
const CAPABILITY_OPTIONS = ["code", "audit", "research", "writing", "design"] as const;

export default function NewJobPage() {
  const router = useRouter();
  const { walletSession } = useAuth();

  // Require auth: redirect to landing if wallet not connected
  useEffect(() => {
    if (!walletSession?.address) {
      router.push("/");
    }
  }, [walletSession?.address, router]);

  const form = useForm<PostJobValues>({
    resolver: zodResolver(postJobSchema),
    defaultValues: {
      title: "",
      description: "",
      capabilities: [],
      payment_token: "USDC", // GAP: no env default provided; using USDC per Section 12.1 examples
      escrow_amount: "",
      // Deadline must be ISO for the schema, but input provides local datetime; we coerce on submit.
      deadline: new Date(Date.now() + 3 * 24 * 60 * 60 * 1000).toISOString(),
    },
  });

  const isSubmitting = form.formState.isSubmitting;

  async function onSubmit(values: PostJobValues) {
    // Convert the UI datetime-local string to ISO. If browser provides full ISO already, Date handles it.
    const isoDeadline = new Date(values.deadline).toISOString();

    const payload = {
      title: values.title.trim(),
      description: values.description.trim(),
      capabilities: values.capabilities.map((c) => c.trim().toLowerCase()),
      payment_token: values.payment_token.trim(),
      escrow_amount: values.escrow_amount.trim(),
      deadline: isoDeadline,
    } satisfies Omit<PostJobValues, "deadline"> & { deadline: string };

    const res = await fetch("/v1/jobs", {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(text || "Failed to create job");
    }

    router.push("/jobs");
  }

  // Map ISO default to input[type=datetime-local] value shape (YYYY-MM-DDTHH:mm)
  const deadlineIso = form.watch("deadline");
  const deadlineLocal = (() => {
    try {
      const d = new Date(deadlineIso);
      const pad = (n: number) => n.toString().padStart(2, "0");
      const yyyy = d.getFullYear();
      const mm = pad(d.getMonth() + 1);
      const dd = pad(d.getDate());
      const hh = pad(d.getHours());
      const mi = pad(d.getMinutes());
      return `${yyyy}-${mm}-${dd}T${hh}:${mi}`;
    } catch {
      return "";
    }
  })();

  return (
    <div className="mx-auto max-w-2xl p-4">
      <h1 className="mb-4 text-2xl font-semibold text-body">Post a Job</h1>
      <Card className="bg-surface shadow-none">
        <form onSubmit={form.handleSubmit(onSubmit)} className="flex flex-col gap-5" noValidate>
          {/* Title */}
          <div className="flex flex-col gap-2">
            <label htmlFor="title" className="text-sm font-medium text-body">
              Title
            </label>
            <Input
              id="title"
              placeholder="e.g. Build an indexing subgraph"
              autoComplete="off"
              {...form.register("title")}
              aria-invalid={!!form.formState.errors.title}
              disabled={isSubmitting}
            />
            {form.formState.errors.title && (
              <p className="text-sm text-error" role="alert">
                {form.formState.errors.title.message}
              </p>
            )}
          </div>

          {/* Description */}
          <div className="flex flex-col gap-2">
            <label htmlFor="description" className="text-sm font-medium text-body">
              Description
            </label>
            <textarea
              id="description"
              placeholder="Describe the task, acceptance criteria, deliverables, and constraints"
              className="min-h-[140px] w-full rounded-md border border-border bg-surface-elevated px-3 py-2 text-body focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
              {...form.register("description")}
              aria-invalid={!!form.formState.errors.description}
              disabled={isSubmitting}
            />
            {form.formState.errors.description && (
              <p className="text-sm text-error" role="alert">
                {form.formState.errors.description.message}
              </p>
            )}
          </div>

          {/* Capabilities */}
          <div className="flex flex-col gap-2">
            <span className="text-sm font-medium text-body">Capabilities</span>
            <div className="flex flex-wrap gap-4">
              {CAPABILITY_OPTIONS.map((cap) => (
                <label key={cap} className="inline-flex items-center gap-2 text-sm text-body">
                  <input
                    type="checkbox"
                    value={cap}
                    className="h-4 w-4 rounded border-border bg-surface-elevated text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
                    {...form.register("capabilities")}
                    disabled={isSubmitting}
                  />
                  <span className="capitalize">{cap}</span>
                </label>
              ))}
            </div>
            {form.formState.errors.capabilities && (
              <p className="text-sm text-error" role="alert">
                {form.formState.errors.capabilities.message as string}
              </p>
            )}
          </div>

          {/* Payment token */}
          <div className="flex flex-col gap-2">
            <label htmlFor="payment_token" className="text-sm font-medium text-body">
              Payment token
            </label>
            <select
              id="payment_token"
              className="w-full rounded-md border border-border bg-surface-elevated px-3 py-2 text-body focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
              {...form.register("payment_token")}
              aria-invalid={!!form.formState.errors.payment_token}
              disabled={isSubmitting}
            >
              <option value="USDC">USDC</option>
            </select>
            {form.formState.errors.payment_token && (
              <p className="text-sm text-error" role="alert">
                {form.formState.errors.payment_token.message as string}
              </p>
            )}
          </div>

          {/* Escrow amount */}
          <div className="flex flex-col gap-2">
            <label htmlFor="escrow_amount" className="text-sm font-medium text-body">
              Escrow amount
            </label>
            <Input
              id="escrow_amount"
              placeholder="e.g. 120 USDC"
              autoComplete="off"
              {...form.register("escrow_amount")}
              aria-invalid={!!form.formState.errors.escrow_amount}
              disabled={isSubmitting}
            />
            {form.formState.errors.escrow_amount && (
              <p className="text-sm text-error" role="alert">
                {form.formState.errors.escrow_amount.message as string}
              </p>
            )}
          </div>

          {/* Deadline */}
          <div className="flex flex-col gap-2">
            <label htmlFor="deadline" className="text-sm font-medium text-body">
              Deadline
            </label>
            <input
              id="deadline"
              type="datetime-local"
              className="w-full rounded-md border border-border bg-surface-elevated px-3 py-2 text-body focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
              value={deadlineLocal}
              onChange={(e) => {
                const local = e.target.value;
                // Convert local datetime (no TZ) to ISO, keep in form state for validation and submission
                const iso = new Date(local).toISOString();
                form.setValue("deadline", iso, { shouldValidate: true });
              }}
              aria-invalid={!!form.formState.errors.deadline}
              disabled={isSubmitting}
            />
            {form.formState.errors.deadline && (
              <p className="text-sm text-error" role="alert">
                {form.formState.errors.deadline.message as string}
              </p>
            )}
          </div>

          {/* Submission */}
          <div className="flex items-center justify-between">
            <p className="text-xs text-muted">GAP: On-chain escrow payment via Wagmi not implemented in this step.</p>
            <Button type="submit" className="min-w-[160px]" disabled={isSubmitting} aria-busy={isSubmitting}>
              {isSubmitting ? "Posting..." : "Post Job"}
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
}

