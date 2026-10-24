import { useId, useRef, useState, type ReactNode } from "react";
import { ArrowUpRight, AudioLines, FileAudio, Upload, X } from "lucide-react";
import { duration, size } from "../api";
import type { AudioItem } from "../types";

export function Panel({
  title,
  step,
  aside,
  children,
  className = "",
}: {
  title: string;
  step?: string;
  aside?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={`panel ${className}`}>
      <div className="panel-heading">
        <h2>
          {step && <span className="step">{step}</span>}
          {title}
        </h2>
        {aside}
      </div>
      {children}
    </section>
  );
}

export function Dropzone({
  accept,
  multiple = true,
  onFiles,
  busy,
  title,
  subtitle,
}: {
  accept: string;
  multiple?: boolean;
  onFiles: (files: File[]) => void;
  busy?: string;
  title: string;
  subtitle: string;
}) {
  const input = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  return (
    <div
      className={`dropzone ${dragging ? "dragging" : ""}`}
      onDragOver={(event) => {
        event.preventDefault();
        setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={(event) => {
        event.preventDefault();
        setDragging(false);
        if (!busy) onFiles(Array.from(event.dataTransfer.files));
      }}
    >
      <input
        ref={input}
        className="visually-hidden"
        type="file"
        accept={accept}
        multiple={multiple}
        disabled={!!busy}
        aria-label={title}
        onChange={(event) => {
          onFiles(Array.from(event.target.files ?? []));
          event.target.value = "";
        }}
      />
      <div className="upload-symbol">
        <Upload size={24} strokeWidth={1.5} />
      </div>
      <h3>{busy || title}</h3>
      <p>{subtitle}</p>
      <button
        type="button"
        className="button secondary"
        disabled={!!busy}
        onClick={() => input.current?.click()}
      >
        {busy ? "Wird übertragen …" : "Dateien auswählen"}
        <ArrowUpRight size={15} />
      </button>
    </div>
  );
}

export function AudioRow({
  item,
  onRemove,
  selected,
  onSelect,
}: {
  item: AudioItem;
  onRemove?: () => void;
  selected?: boolean;
  onSelect?: () => void;
}) {
  return (
    <div className={`audio-row ${selected ? "selected" : ""}`}>
      {onSelect ? (
        <input
          type="checkbox"
          checked={selected}
          onChange={onSelect}
          aria-label={`${item.name} auswählen`}
        />
      ) : (
        <div className="file-icon">
          <FileAudio size={19} />
        </div>
      )}
      <div className="audio-info">
        <strong title={item.name}>{item.name}</strong>
        <span>
          {duration(item.duration)} <i>·</i> {item.sample_rate / 1000} kHz{" "}
          <i>·</i> {size(item.size)}
        </span>
        <audio
          controls
          preload="none"
          src={`/api/audio/${item.id}/file`}
          aria-label={`${item.name} anhören`}
        />
      </div>
      {onRemove && (
        <button
          type="button"
          className="icon-button"
          aria-label={`${item.name} entfernen`}
          onClick={onRemove}
        >
          <X size={16} />
        </button>
      )}
    </div>
  );
}

export function Slider({
  label,
  value,
  min,
  max,
  step = 0.01,
  onChange,
  hint,
  unit = "",
}: {
  label: string;
  value: number;
  min: number;
  max: number;
  step?: number;
  onChange: (value: number) => void;
  hint?: string;
  unit?: string;
}) {
  const id = useId();
  return (
    <div className="slider-control">
      <div>
        <label htmlFor={id}>{label}</label>
        <output htmlFor={id}>
          {Number(value.toFixed(2))}
          {unit}
        </output>
      </div>
      <input
        id={id}
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(event) => onChange(Number(event.target.value))}
      />
      {hint && <p>{hint}</p>}
    </div>
  );
}

export function Empty({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <div className="empty">
      <AudioLines size={30} strokeWidth={1.25} />
      <h3>{title}</h3>
      <p>{children}</p>
    </div>
  );
}

export function Toggle({
  checked,
  onChange,
  title,
  description,
}: {
  checked: boolean;
  onChange: (value: boolean) => void;
  title: string;
  description: string;
}) {
  return (
    <label className="toggle-row">
      <span>
        <strong>{title}</strong>
        <small>{description}</small>
      </span>
      <input
        type="checkbox"
        role="switch"
        checked={checked}
        onChange={(event) => onChange(event.target.checked)}
      />
      <span className="switch" aria-hidden="true" />
    </label>
  );
}
