"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";

import Button from "@/components/ui/Button";
import Card from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";

export const bidFormSchema = z.object({
  proposed_amount: z.string().min(1, "Amount is required"),
  message: z.string().optional(),
});

export type BidFormValues = z.infer<typeof bidFormSchema>;

type BidFormProps = {
  jobId: string;
  onSubmitted?: () => void;
  disabled?: boolean;
};

export function BidForm({ jobId, onSubmitted, disabled }: BidFormProps) {
  const queryClient = useQueryClient();
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const form = useForm<BidFormValues>({
    resolver: zodResolver(bidFormSchema),
    defaultValues: {
      proposed_amount: "",
      message: "",
    },
  });

  const isSubmitting = form.formState.isSubmitting;

  const onSubmit = async (values: BidFormValues) => {
    setSubmitError(null);
    setSuccessMessage(null);

    const payload = {
      proposed_amount: values.proposed_amount.trim(),
      message: values.message?.trim() ?? "",
      // GAP: axl_message_id generation is unspecified in the blueprint. Sending null per Section 8.4 until upstream flow is defined.
      axl_message_id: null,
    };

    try {
      const res = await fetch(`/v1/jobs/${jobId}/bids`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errorText = await res.text();
        throw new Error(errorText || "Failed to submit bid");
      }

      setSuccessMessage("Bid submitted");
      form.reset();
      await queryClient.invalidateQueries({ queryKey: ["job", jobId] });
      onSubmitted?.();
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to submit bid";
      setSubmitError(message);
    }
  };

  return (
    <Card className="bg-surface shadow-none">
      <form className="flex flex-col gap-4" onSubmit={form.handleSubmit(onSubmit)}>
        <div className="flex flex-col gap-2">
          <label className="text-sm font-medium text-body" htmlFor="proposed_amount">
            Proposed amount
          </label>
          <Input
            id="proposed_amount"
            type="text"
            inputMode="decimal"
            autoComplete="off"
            placeholder="e.g. 120 USDC"
            {...form.register("proposed_amount")}
            aria-invalid={!!form.formState.errors.proposed_amount}
            disabled={disabled || isSubmitting}
          />
          {form.formState.errors.proposed_amount && (
            <p className="text-sm text-error" role="alert">
              {form.formState.errors.proposed_amount.message}
            </p>
          )}
        </div>

        <div className="flex flex-col gap-2">
          <label className="text-sm font-medium text-body" htmlFor="message">
            Message (optional)
          </label>
          <textarea
            id="message"
            rows={4}
            className="w-full rounded-md border border-border bg-surface-elevated px-3 py-2 text-body shadow-none transition-colors duration-200 ease-in-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
            placeholder="Describe your approach, timeline, or milestones"
            {...form.register("message")}
            aria-invalid={!!form.formState.errors.message}
            disabled={disabled || isSubmitting}
          />
          {form.formState.errors.message && (
            <p className="text-sm text-error" role="alert">
              {form.formState.errors.message.message}
            </p>
          )}
        </div>

        {submitError && (
          <div className="rounded-md border border-error/50 bg-error/10 p-3 text-sm text-error" role="alert">
            {submitError}
          </div>
        )}

        {successMessage && (
          <div className="rounded-md border border-success/50 bg-success/10 p-3 text-sm text-success" role="status">
            {successMessage}
          </div>
        )}

        <div className="flex justify-end">
          <Button
            type="submit"
            className="min-w-[140px]"
            disabled={disabled || isSubmitting}
            aria-busy={isSubmitting}
          >
            {isSubmitting ? "Submitting..." : "Submit bid"}
          </Button>
        </div>
      </form>
    </Card>
  );
}

export default BidForm;
