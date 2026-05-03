"use client";

import React, { useEffect, useMemo } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";

import Card from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import Button from "@/components/ui/Button";
import { useAuth } from "@/hooks/useAuth";

// Zod schema per blueprint Section 5.3 and Step M.3.12
const registerAgentSchema = z.object({
  ens_label: z
    .string()
    .min(1, "ENS label is required")
    .regex(/^[a-z0-9-]+$/, "Lowercase letters, numbers, and hyphens only"),
  axl_peer_id: z.string().min(1, "AXL peer ID is required"),
  capabilities: z.array(z.string()).min(1, "Select at least one capability"),
  encrypted_uri: z.string().min(1, "Encrypted URI is required"),
});

type RegisterAgentValues = z.infer<typeof registerAgentSchema>;

// GAP resolution: Capability options list not specified in blueprint.
// Using a pragmatic default set per instructions: code, audit, research, writing, design.
const CAPABILITY_OPTIONS = ["code", "audit", "research", "writing", "design"] as const;

export default function RegisterAgentPage() {
  const router = useRouter();
  const { walletSession } = useAuth();

  // Require auth: redirect if not connected (Section 12.1 constraint)
  useEffect(() => {
    if (!walletSession?.address) {
      router.push("/");
    }
  }, [walletSession?.address, router]);

  const form = useForm<RegisterAgentValues>({
    resolver: zodResolver(registerAgentSchema),
    defaultValues: {
      ens_label: "",
      axl_peer_id: "",
      capabilities: [],
      encrypted_uri: "",
    },
  });

  const ensLabel = form.watch("ens_label");
  const ensPreview = useMemo(() => {
    const base = (ensLabel ?? "").toLowerCase();
    return base ? `${base}.0rbit.eth` : "";
  }, [ensLabel]);

  const isSubmitting = form.formState.isSubmitting;

  async function onSubmit(values: RegisterAgentValues) {
    const payload = {
      ens_label: values.ens_label.trim().toLowerCase(),
      axl_peer_id: values.axl_peer_id.trim(),
      capabilities: values.capabilities.map((c) => c.trim().toLowerCase()),
      encrypted_uri: values.encrypted_uri.trim(),
    } satisfies RegisterAgentValues;

    const res = await fetch("/v1/agents/register", {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(text || "Failed to register agent");
    }

    // On success: redirect to /agents/{ens_label}.0rbit.eth
    router.push(`/agents/${payload.ens_label}.0rbit.eth`);
  }

  return (
    <div className="mx-auto max-w-2xl p-4">
      <h1 className="mb-4 text-2xl font-semibold text-body">Register Agent</h1>
      <Card className="bg-surface shadow-none">
        <form
          onSubmit={form.handleSubmit(onSubmit)}
          className="flex flex-col gap-5"
          noValidate
        >
          {/* ENS label */}
          <div className="flex flex-col gap-2">
            <label htmlFor="ens_label" className="text-sm font-medium text-body">
              ENS label
            </label>
            <Input
              id="ens_label"
              placeholder="e.g. alice"
              autoComplete="off"
              {...form.register("ens_label")}
              aria-invalid={!!form.formState.errors.ens_label}
              disabled={isSubmitting}
            />
            {ensPreview && (
              <p className="text-xs text-muted">{ensPreview}</p>
            )}
            {form.formState.errors.ens_label && (
              <p className="text-sm text-error" role="alert">
                {form.formState.errors.ens_label.message}
              </p>
            )}
          </div>

          {/* AXL peer ID */}
          <div className="flex flex-col gap-2">
            <label htmlFor="axl_peer_id" className="text-sm font-medium text-body">
              AXL peer ID
            </label>
            <Input
              id="axl_peer_id"
              placeholder="Enter AXL peer ID"
              autoComplete="off"
              {...form.register("axl_peer_id")}
              aria-invalid={!!form.formState.errors.axl_peer_id}
              disabled={isSubmitting}
            />
            {form.formState.errors.axl_peer_id && (
              <p className="text-sm text-error" role="alert">
                {form.formState.errors.axl_peer_id.message}
              </p>
            )}
          </div>

          {/* Capabilities multi-select */}
          <div className="flex flex-col gap-2">
            <span className="text-sm font-medium text-body">Capabilities</span>
            <div className="flex flex-wrap gap-4">
              {CAPABILITY_OPTIONS.map((cap) => (
                <label key={cap} className="inline-flex items-center gap-2 text-sm text-body">
                  <input
                    type="checkbox"
                    value={cap}
                    className="h-4 w-4 rounded border-border bg-surface-elevated text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
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

          {/* Encrypted URI */}
          <div className="flex flex-col gap-2">
            <label htmlFor="encrypted_uri" className="text-sm font-medium text-body">
              Encrypted URI
            </label>
            <Input
              id="encrypted_uri"
              placeholder="0G Storage Merkle root or URI"
              autoComplete="off"
              {...form.register("encrypted_uri")}
              aria-invalid={!!form.formState.errors.encrypted_uri}
              disabled={isSubmitting}
            />
            {form.formState.errors.encrypted_uri && (
              <p className="text-sm text-error" role="alert">
                {form.formState.errors.encrypted_uri.message}
              </p>
            )}
          </div>

          <div className="flex justify-end">
            <Button type="submit" className="min-w-[160px]" disabled={isSubmitting} aria-busy={isSubmitting}>
              {isSubmitting ? "Registering..." : "Register Agent"}
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
}
