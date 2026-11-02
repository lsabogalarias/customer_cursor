import { FormEvent, useEffect, useState } from "react";
import { ApiError, apiRequest } from "../api/client";
import { useAuth } from "../auth/AuthProvider";
import type { AgentCall, AgentMessage, Claim, Driver, Policy, Vehicle } from "../types";
import { isAutoPolicy } from "../types";

/**
 * Messages, mock calls, and policy changes from the contact section.
 *
 * @returns The Contact Agent page.
 */
export function Contact() {
  const { token } = useAuth();
  const [policies, setPolicies] = useState<Policy[]>([]);
  const [policyNumber, setPolicyNumber] = useState("");
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [messages, setMessages] = useState<AgentMessage[]>([]);
  const [calls, setCalls] = useState<AgentCall[]>([]);
  const [body, setBody] = useState("");
  const [phone, setPhone] = useState("+1 512 555 0142");
  const [year, setYear] = useState("2021");
  const [make, setMake] = useState("");
  const [model, setModel] = useState("");
  const [vin, setVin] = useState("");
  const [driverName, setDriverName] = useState("");
  const [licenseNumber, setLicenseNumber] = useState("");
  const [dateOfBirth, setDateOfBirth] = useState("1990-01-15");
  const [description, setDescription] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      return;
    }
    Promise.all([
      apiRequest<{ policies: Policy[] }>("/api/policies", {}, token),
      apiRequest<{ messages: AgentMessage[] }>("/api/contact/messages", {}, token),
      apiRequest<{ calls: AgentCall[] }>("/api/contact/calls", {}, token),
    ])
      .then(([policyPayload, messagePayload, callPayload]) => {
        setPolicies(policyPayload.policies);
        setPolicyNumber((current) => current || policyPayload.policies[0]?.policy_number || "");
        setMessages(messagePayload.messages);
        setCalls(callPayload.calls);
      })
      .catch((caught: unknown) => {
        setError(caught instanceof ApiError ? caught.message : "Contact details could not be loaded.");
      });
  }, [token]);

  useEffect(() => {
    if (!token || !policyNumber || !isAutoPolicy(policyNumber)) {
      setVehicles([]);
      setDrivers([]);
      return;
    }
    Promise.all([
      apiRequest<{ vehicles: Vehicle[] }>(`/api/policies/${policyNumber}/vehicles`, {}, token),
      apiRequest<{ drivers: Driver[] }>(`/api/policies/${policyNumber}/drivers`, {}, token),
    ])
      .then(([vehiclePayload, driverPayload]) => {
        setVehicles(vehiclePayload.vehicles);
        setDrivers(driverPayload.drivers);
      })
      .catch((caught: unknown) => {
        setError(caught instanceof ApiError ? caught.message : "Policy details could not be loaded.");
      });
  }, [token, policyNumber]);

  async function sendMessage(event: FormEvent): Promise<void> {
    event.preventDefault();
    if (!token) {
      return;
    }
    setError(null);
    try {
      const created = await apiRequest<AgentMessage>(
        "/api/contact/messages",
        { method: "POST", body: JSON.stringify({ body }) },
        token,
      );
      setMessages((current) => [...current, created]);
      setBody("");
      setNotice(`Message sent. Reference ${created.twilio_sid}.`);
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "The message could not be sent.");
    }
  }

  async function startCall(event: FormEvent): Promise<void> {
    event.preventDefault();
    if (!token) {
      return;
    }
    setError(null);
    try {
      const created = await apiRequest<AgentCall>(
        "/api/contact/calls",
        { method: "POST", body: JSON.stringify({ phone_number: phone }) },
        token,
      );
      setCalls((current) => [...current, created]);
      setNotice(`Call requested. Reference ${created.twilio_sid}.`);
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "The call could not be started.");
    }
  }

  async function renew(): Promise<void> {
    if (!token || !policyNumber) {
      return;
    }
    setError(null);
    try {
      await apiRequest<Policy>(`/api/policies/${policyNumber}/renew`, { method: "POST" }, token);
      setNotice(`Renewal requested for ${policyNumber}.`);
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Renewal could not be requested.");
    }
  }

  async function addVehicle(event: FormEvent): Promise<void> {
    event.preventDefault();
    if (!token) {
      return;
    }
    try {
      const created = await apiRequest<Vehicle>(
        `/api/policies/${policyNumber}/vehicles`,
        { method: "POST", body: JSON.stringify({ year: Number(year), make, model, vin }) },
        token,
      );
      setVehicles((current) => [...current, created]);
      setNotice("Vehicle added.");
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "The vehicle could not be added.");
    }
  }

  async function removeVehicle(vehicleId: string): Promise<void> {
    if (!token) {
      return;
    }
    await apiRequest(`/api/policies/${policyNumber}/vehicles/${vehicleId}`, { method: "DELETE" }, token);
    setVehicles((current) => current.filter((item) => item.vehicle_id !== vehicleId));
  }

  async function addDriver(event: FormEvent): Promise<void> {
    event.preventDefault();
    if (!token) {
      return;
    }
    try {
      const created = await apiRequest<Driver>(
        `/api/policies/${policyNumber}/drivers`,
        {
          method: "POST",
          body: JSON.stringify({
            full_name: driverName,
            license_number: licenseNumber,
            date_of_birth: dateOfBirth,
          }),
        },
        token,
      );
      setDrivers((current) => [...current, created]);
      setNotice("Driver added.");
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "The driver could not be added.");
    }
  }

  async function removeDriver(driverId: string): Promise<void> {
    if (!token) {
      return;
    }
    await apiRequest(`/api/policies/${policyNumber}/drivers/${driverId}`, { method: "DELETE" }, token);
    setDrivers((current) => current.filter((item) => item.driver_id !== driverId));
  }

  async function submitClaim(event: FormEvent): Promise<void> {
    event.preventDefault();
    if (!token) {
      return;
    }
    try {
      const created = await apiRequest<Claim>(
        `/api/policies/${policyNumber}/claims`,
        { method: "POST", body: JSON.stringify({ description }) },
        token,
      );
      setDescription("");
      setNotice(`Claim ${created.claim_id.slice(0, 8)} submitted.`);
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "The claim could not be submitted.");
    }
  }

  const auto = isAutoPolicy(policyNumber);

  return (
    <section>
      <header className="page-head">
        <p className="eyebrow">Agent</p>
        <h1>Contact Agent</h1>
        <p>Messages and calls use a mock Twilio provider. Nothing is sent to a phone network.</p>
      </header>
      {notice ? <p className="banner banner-ok">{notice}</p> : null}
      {error ? <p className="banner banner-error">{error}</p> : null}
      <div className="split">
        <form className="card stack-form" onSubmit={(event) => void sendMessage(event)}>
          <h2>Send a message</h2>
          <label>
            Message
            <textarea value={body} onChange={(event) => setBody(event.target.value)} required />
          </label>
          <button type="submit" className="btn btn-primary">
            Send message
          </button>
          <ul className="plain-list">
            {messages.map((message) => (
              <li key={message.message_id}>
                <span>{message.body}</span>
                <span className="muted">{message.twilio_sid.slice(0, 10)}</span>
              </li>
            ))}
          </ul>
        </form>
        <form className="card stack-form" onSubmit={(event) => void startCall(event)}>
          <h2>Request a call</h2>
          <label>
            Phone number
            <input value={phone} onChange={(event) => setPhone(event.target.value)} required />
          </label>
          <button type="submit" className="btn btn-primary">
            Call
          </button>
          <ul className="plain-list">
            {calls.map((call) => (
              <li key={call.call_id}>
                <span>{call.phone_number}</span>
                <span className="muted">{call.twilio_sid.slice(0, 10)}</span>
              </li>
            ))}
          </ul>
        </form>
      </div>
      <section className="card">
        <h2>Policy changes</h2>
        <label>
          Policy
          <select value={policyNumber} onChange={(event) => setPolicyNumber(event.target.value)}>
            {policies.map((policy) => (
              <option key={policy.policy_number} value={policy.policy_number}>
                {policy.policy_number} · {policy.product_name}
              </option>
            ))}
          </select>
        </label>
        <div className="actions">
          <button type="button" className="btn btn-primary" onClick={() => void renew()}>
            Renew policy
          </button>
        </div>
        {auto ? (
          <div className="split">
            <form className="stack-form" onSubmit={(event) => void addVehicle(event)}>
              <h3>Vehicles</h3>
              <ul className="plain-list">
                {vehicles.map((vehicle) => (
                  <li key={vehicle.vehicle_id}>
                    <span>
                      {vehicle.year} {vehicle.make} {vehicle.model}
                    </span>
                    <button type="button" className="btn btn-secondary" onClick={() => void removeVehicle(vehicle.vehicle_id)}>
                      Remove
                    </button>
                  </li>
                ))}
              </ul>
              <label>
                Year
                <input value={year} onChange={(event) => setYear(event.target.value)} required />
              </label>
              <label>
                Make
                <input value={make} onChange={(event) => setMake(event.target.value)} required />
              </label>
              <label>
                Model
                <input value={model} onChange={(event) => setModel(event.target.value)} required />
              </label>
              <label>
                VIN
                <input value={vin} onChange={(event) => setVin(event.target.value)} required />
              </label>
              <button type="submit" className="btn btn-secondary">
                Add vehicle
              </button>
            </form>
            <form className="stack-form" onSubmit={(event) => void addDriver(event)}>
              <h3>Drivers</h3>
              <ul className="plain-list">
                {drivers.map((driver) => (
                  <li key={driver.driver_id}>
                    <span>{driver.full_name}</span>
                    <button type="button" className="btn btn-secondary" onClick={() => void removeDriver(driver.driver_id)}>
                      Remove
                    </button>
                  </li>
                ))}
              </ul>
              <label>
                Full name
                <input value={driverName} onChange={(event) => setDriverName(event.target.value)} required />
              </label>
              <label>
                License number
                <input value={licenseNumber} onChange={(event) => setLicenseNumber(event.target.value)} required />
              </label>
              <label>
                Date of birth
                <input type="date" value={dateOfBirth} onChange={(event) => setDateOfBirth(event.target.value)} required />
              </label>
              <button type="submit" className="btn btn-secondary">
                Add driver
              </button>
            </form>
          </div>
        ) : (
          <p>Vehicles and drivers can be changed on auto and truck policies only.</p>
        )}
        <form className="stack-form" onSubmit={(event) => void submitClaim(event)}>
          <h3>Submit a claim</h3>
          <label>
            What happened
            <textarea value={description} onChange={(event) => setDescription(event.target.value)} required minLength={10} />
          </label>
          <button type="submit" className="btn btn-primary">
            Submit claim
          </button>
        </form>
      </section>
    </section>
  );
}
