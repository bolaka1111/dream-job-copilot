import React from "react";
import { ExternalLink } from "lucide-react";
import Button from "./common/Button";

/**
 * "Apply on [Portal]" button — always visible on every job card.
 * Per guardrails §4: primary CTA, always visible without expanding.
 */
export default React.memo(function ApplyButton({ url, source, className }) {
  const portalName = source || "Job Portal";

  if (!url) return null;

  return (
    <Button
      variant="primary"
      size="sm"
      icon={ExternalLink}
      className={className}
      onClick={(e) => {
        e.stopPropagation();
        window.open(url, "_blank", "noopener,noreferrer");
      }}
      aria-label={`Apply on ${portalName}`}
    >
      Apply on {portalName}
    </Button>
  );
});
