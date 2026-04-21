// Example policy. Not production-ready. Adapt to your own schema and tenant model.
// Deny calls to send_email whose "to" address is outside the org domain.

forbid (
    principal,
    action == Action::"tool.invoke",
    resource is Tool
)
when {
    resource.name == "send_email" &&
    !(resource.args["to"] like "*@example.com")
};

// Require human approval for any tool invocation with a "customer_id" arg
// belonging to the restricted segment.
@id("approval.customer.restricted")
permit (
    principal,
    action == Action::"tool.invoke",
    resource is Tool
)
when {
    resource.args has "customer_id" &&
    resource.args["customer_id"] like "restricted-*"
}
advice {
    kind: "require_approval",
    rationale: "Restricted customer segment requires a reviewer sign-off."
};
