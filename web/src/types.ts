/** Public shapes returned by the API gateway. */

export interface UserProfile {
  user_id: string;
  email: string;
  full_name: string;
}

export interface Policy {
  policy_number: string;
  line_of_business: "personal_auto" | "truck" | "homeowners";
  product_name: string;
  status: "active" | "renewal_requested";
  insured_name: string;
  property_address: string | null;
  effective_date: string;
  expiration_date: string;
  premium: string;
}

export interface Vehicle {
  vehicle_id: string;
  policy_number: string;
  year: number;
  make: string;
  model: string;
  vin: string;
}

export interface Driver {
  driver_id: string;
  policy_number: string;
  full_name: string;
  license_number: string;
  date_of_birth: string;
}

export interface PolicyDocument {
  document_id: string;
  policy_number: string;
  title: string;
  file_name: string;
  content_type: string;
}

export interface Claim {
  claim_id: string;
  policy_number: string;
  description: string;
  status: string;
  filed_at: string;
}

export interface RenewalQuote {
  policy_number: string;
  current_premium: string;
  renewal_premium: string;
  renewal_effective_date: string;
  status: string;
}

export interface IdCard {
  policy_number: string;
  insured_name: string;
  line_of_business: string;
  effective_date: string;
  expiration_date: string;
  property_address: string | null;
  vehicles: Vehicle[];
}

export interface Payment {
  payment_id: string;
  policy_number: string;
  amount: string;
  status: "paid" | "pending";
  due_date: string;
  description: string;
  paid_at: string | null;
  confirmation_id: string | null;
}

export interface AgentMessage {
  message_id: string;
  body: string;
  created_at: string;
  twilio_sid: string;
}

export interface AgentCall {
  call_id: string;
  phone_number: string;
  created_at: string;
  twilio_sid: string;
}

/**
 * Format a string premium as US dollars.
 *
 * @param amount - Decimal string from the API, such as "1280.00".
 * @returns A dollar label.
 */
export function formatMoney(amount: string): string {
  return `$${amount}`;
}

/**
 * Turn a status code into an English label.
 *
 * @param status - API status value.
 * @returns Label for the screen.
 */
export function formatStatus(status: string): string {
  if (status === "renewal_requested") {
    return "Renewal requested";
  }
  if (status === "active") {
    return "Active";
  }
  if (status === "paid") {
    return "Paid";
  }
  if (status === "pending") {
    return "Pending";
  }
  if (status === "submitted") {
    return "Submitted";
  }
  return status;
}

/**
 * Tell whether a policy number is an auto or truck policy.
 *
 * @param policyNumber - Policy number such as AUTO-1001.
 * @returns True when vehicles and drivers apply.
 */
export function isAutoPolicy(policyNumber: string): boolean {
  return policyNumber.startsWith("AUTO-");
}
