import { FormEvent, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ApiError, apiRequest } from "../api/client";
import { useAuth } from "../auth/AuthProvider";
import type { Claim, Driver, Policy, Vehicle } from "../types";
import { formatStatus, isAutoPolicy } from "../types";

/**
 * Manage vehicles, drivers, and claims for one policy.
 *
 * @returns The manage page.
 */
export function ManagePolicy() {
  const { policyNumber = "" } = useParams();
  const { token } = useAuth();
  const [policy, setPolicy] = useState<Policy | null>(null);
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [claims, setClaims] = useState<Claim[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [year, setYear] = useState("2021");
  const [make, setMake] = useState("");
  const [model, setModel] = useState("");
  const [vin, setVin] = useState("");
  const [driverName, setDriverName] = useState("");
  const [licenseNumber, setLicenseNumber] = useState("");
  const [dateOfBirth, setDateOfBirth] = useState("1990-01-15");
  const [description, setDescription] = useState("");

  useEffect(() => {
    if (!token || !policyNumber) {
      return;
    }
    const currentToken = token;
    async function load(): Promise<void> {
      try {
        const [nextPolicy, nextClaims] = await Promise.all([
          apiRequest<Policy>(`/api/policies/${policyNumber}`, {}, currentToken),
          apiRequest<{ claims: Claim[] }>(`/api/policies/${policyNumber}/claims`, {}, currentToken),
        ]);
        setPolicy(nextPolicy);
        setClaims(nextClaims.claims);
        if (isAutoPolicy(nextPolicy.policy_number)) {
          const [nextVehicles, nextDrivers] = await Promise.all([
            apiRequest<{ vehicles: Vehicle[] }>(`/api/policies/${policyNumber}/vehicles`, {}, currentToken),
            apiRequest<{ drivers: Driver[] }>(`/api/policies/${policyNumber}/drivers`, {}, currentToken),
          ]);
          setVehicles(nextVehicles.vehicles);
          setDrivers(nextDrivers.drivers);
        }
      } catch (caught) {
        setError(caught instanceof ApiError ? caught.message : "This policy could not be loaded.");
      }
    }
    void load();
  }, [token, policyNumber]);

  async function addVehicle(event: FormEvent): Promise<void> {
    event.preventDefault();
    if (!token) {
      return;
    }
    setError(null);
    try {
      const created = await apiRequest<Vehicle>(
        `/api/policies/${policyNumber}/vehicles`,
        { method: "POST", body: JSON.stringify({ year: Number(year), make, model, vin }) },
        token,
      );
      setVehicles((current) => [...current, created]);
      setMake("");
      setModel("");
      setVin("");
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
    setError(null);
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
      setDriverName("");
      setLicenseNumber("");
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
    setError(null);
    try {
      const created = await apiRequest<Claim>(
        `/api/policies/${policyNumber}/claims`,
        { method: "POST", body: JSON.stringify({ description }) },
        token,
      );
      setClaims((current) => [...current, created]);
      setDescription("");
      setNotice("Claim submitted.");
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "The claim could not be submitted.");
    }
  }

  const auto = policy ? isAutoPolicy(policy.policy_number) : false;

  return (
    <section>
      <header className="page-head">
        <p className="eyebrow">Manage</p>
        <h1>{policy?.policy_number ?? policyNumber}</h1>
        {policy ? (
          <p>
            {policy.product_name} · {formatStatus(policy.status)}
            {policy.property_address ? ` · ${policy.property_address}` : ""}
          </p>
        ) : null}
        <Link to={`/policies/${policyNumber}/renewal`}>Renewal Details</Link>
      </header>
      {notice ? <p className="banner banner-ok">{notice}</p> : null}
      {error ? <p className="banner banner-error">{error}</p> : null}
      {auto ? (
        <div className="split">
          <section className="card">
            <h2>Vehicles</h2>
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
            <form className="stack-form" onSubmit={(event) => void addVehicle(event)}>
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
              <button type="submit" className="btn btn-primary">
                Add vehicle
              </button>
            </form>
          </section>
          <section className="card">
            <h2>Drivers</h2>
            <ul className="plain-list">
              {drivers.map((driver) => (
                <li key={driver.driver_id}>
                  <span>
                    {driver.full_name} · {driver.license_number}
                  </span>
                  <button type="button" className="btn btn-secondary" onClick={() => void removeDriver(driver.driver_id)}>
                    Remove
                  </button>
                </li>
              ))}
            </ul>
            <form className="stack-form" onSubmit={(event) => void addDriver(event)}>
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
              <button type="submit" className="btn btn-primary">
                Add driver
              </button>
            </form>
          </section>
        </div>
      ) : (
        <p className="banner">Vehicles and drivers apply only to auto and truck policies.</p>
      )}
      <section className="card">
        <h2>Claims</h2>
        <ul className="plain-list">
          {claims.map((claim) => (
            <li key={claim.claim_id}>
              <span>{claim.description}</span>
              <span className="muted">{formatStatus(claim.status)}</span>
            </li>
          ))}
        </ul>
        <form className="stack-form" onSubmit={(event) => void submitClaim(event)}>
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
