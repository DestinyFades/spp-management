'use client';

import { useState, useEffect } from 'react';

interface DateSelectorProps {
  onDateChange: (versionId: number) => void;
}

export function DateSelector({ onDateChange }: DateSelectorProps) {
  const [dates, setDates] = useState<{id: number, date: string}[]>([]);
  const [selectedId, setSelectedId] = useState<number>(1);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://localhost:8000/api/v1/dates')
      .then(res => {
        if (!res.ok) throw new Error('HTTP ' + res.status);
        return res.json();
      })
      .then(data => {
        setDates(data);
        if (data.length > 0) {
          setSelectedId(data[0].id);
          onDateChange(data[0].id);
        }
        setLoading(false);
      })
      .catch(err => {
        console.error('Ошибка загрузки дат:', err);
        setLoading(false);
      });
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const id = parseInt(e.target.value);
    setSelectedId(id);
    onDateChange(id);
  };

  if (loading) {
    return <div>⏳ Загрузка дат...</div>;
  }

  if (dates.length === 0) {
    return <div>❌ Нет доступных дат</div>;
  }

  return (
    <div style={{ marginBottom: '1rem' }}>
      <label style={{ marginRight: '0.5rem', fontWeight: 'bold' }}>
        📅 Выберите дату:
      </label>
      <select
        value={selectedId}
        onChange={handleChange}
        style={{ 
          padding: '0.5rem', 
          borderRadius: '4px', 
          border: '1px solid #ccc',
          fontSize: '1rem',
          minWidth: '200px'
        }}
      >
        {dates.map((d) => (
          <option key={d.id} value={d.id}>
            {d.date}
          </option>
        ))}
      </select>
    </div>
  );
}
