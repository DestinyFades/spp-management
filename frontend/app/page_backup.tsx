'use client';

import { useState, useEffect } from 'react';
import { DateSelector } from './components/DateSelector';

export default function Home() {
  const [treeData, setTreeData] = useState<any>(null);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [versionId, setVersionId] = useState<number>(1);
  const [totalAmount, setTotalAmount] = useState<string>('1000');
  const [calcResult, setCalcResult] = useState<any>(null);
  const [savedList, setSavedList] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  // Загрузка дерева по версии
  const loadTree = async (vid: number) => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/v1/tree/' + vid);
      if (response.ok) {
        const data = await response.json();
        setTreeData(data);
        setVersionId(vid);
      } else {
        console.error('Ошибка загрузки дерева:', response.status);
      }
    } catch (err) {
      console.error('Ошибка загрузки дерева:', err);
    } finally {
      setLoading(false);
    }
  };

  // Загрузка сохраненных расчетов
  const loadSaved = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/saved/default');
      if (response.ok) {
        const data = await response.json();
        setSavedList(data);
      }
    } catch (err) {
      console.error('Ошибка загрузки сохраненных расчетов:', err);
    }
  };

  // Загрузка сохраненного расчета в дерево (ЗАДАЧА 10)
  const loadSavedCalculation = async (calcId: number) => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/saved/' + calcId + '/load');
      if (response.ok) {
        const data = await response.json();
        setTreeData(data.tree);
        alert('✅ Сохраненный расчет загружен в дерево!');
      }
    } catch (err) {
      console.error('Ошибка загрузки сохраненного расчета:', err);
      alert('❌ Ошибка загрузки');
    }
  };

  // Загрузка при первом рендере
  useEffect(() => {
    loadTree(1);
    loadSaved();
  }, []);

  // Обработчик выбора даты
  const handleDateChange = (vid: number) => {
    loadTree(vid);
  };

  // Рендер узла дерева
  const renderNode = (node: any, level: number = 0) => {
    const isChecked = selectedIds.includes(node.id);
    const hasChildren = node.children && node.children.length > 0;
    const marginLeft = level * 1.5;

    return (
      <div key={node.id} style={{ marginLeft: marginLeft + 'rem', marginTop: '0.25rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <input
            type="checkbox"
            checked={isChecked}
            onChange={(e) => {
              if (e.target.checked) {
                setSelectedIds([...selectedIds, node.id]);
              } else {
                setSelectedIds(selectedIds.filter(id => id !== node.id));
              }
            }}
            style={{ width: '1rem', height: '1rem', cursor: 'pointer' }}
          />
          <span style={{ fontWeight: hasChildren ? 'bold' : 'normal' }}>
            {node.code} - {node.name}
          </span>
          {node.allocated !== undefined && (
            <span style={{ color: '#16a34a', fontWeight: 'bold' }}>
              {node.allocated.toFixed(2)} ₽
            </span>
          )}
          {node.departments && node.departments.length > 0 && (
            <span style={{ fontSize: '0.8rem', color: '#666' }}>
              ({node.departments.join(', ')})
            </span>
          )}
        </div>
        {hasChildren && (
          <div style={{ borderLeft: '2px solid #e5e7eb', paddingLeft: '0.5rem' }}>
            {node.children.map((child: any) => renderNode(child, level + 1))}
          </div>
        )}
      </div>
    );
  };

  // Выполнение распределения
  const handleDistribute = async () => {
    if (selectedIds.length === 0) {
      alert('Выберите хотя бы один элемент');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/v1/distribute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          version_id: versionId,
          selected_ids: selectedIds,
          total_amount: parseFloat(totalAmount)
        })
      });

      if (response.ok) {
        const data = await response.json();
        setCalcResult(data);
        setTreeData(data.tree);
        alert('✅ Распределение выполнено!');
      } else {
        const error = await response.json();
        alert('❌ Ошибка: ' + (error.detail || 'Неизвестная ошибка'));
      }
    } catch (err) {
      console.error('Ошибка распределения:', err);
      alert('❌ Ошибка распределения');
    } finally {
      setLoading(false);
    }
  };

  // Сохранение расчета
  const handleSave = async () => {
    if (!calcResult) {
      alert('Сначала выполните распределение');
      return;
    }

    try {
      const response = await fetch('http://localhost:8000/api/v1/save/' + calcResult.calc_id, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: 'default' })
      });

      if (response.ok) {
        const data = await response.json();
        alert('✅ Расчет сохранен в базу данных! ID: ' + data.id);
        setCalcResult(null);
        loadSaved();
      }
    } catch (err) {
      console.error('Ошибка сохранения:', err);
      alert('❌ Ошибка сохранения');
    }
  };

  // Экспорт в Excel
  const handleExport = async (calcId: number) => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/export/' + calcId);
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'calc_' + calcId + '.xlsx';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
      }
    } catch (err) {
      console.error('Ошибка экспорта:', err);
      alert('❌ Ошибка экспорта');
    }
  };

  return (
    <div style={{ 
      padding: '2rem', 
      fontFamily: 'Arial, sans-serif', 
      maxWidth: '1200px', 
      margin: '0 auto',
      minHeight: '100vh',
      background: '#f5f5f5'
    }}>
      <h1 style={{ marginBottom: '1.5rem', color: '#1a1a1a' }}>🚀 SPP Management</h1>
      
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '2rem' }}>
        {/* Левая колонка */}
        <div>
          {/* КОМБОБОКС ВЫБОРА ДАТЫ (ЗАДАЧА 9) */}
          <DateSelector onDateChange={handleDateChange} />
          
          {/* Дерево */}
          <div style={{ 
            padding: '1rem', 
            background: '#fff', 
            border: '1px solid #e5e7eb', 
            borderRadius: '8px',
            minHeight: '400px',
            maxHeight: '600px',
            overflow: 'auto'
          }}>
            {loading ? (
              <div>⏳ Загрузка...</div>
            ) : treeData ? (
              renderNode(treeData)
            ) : (
              <div>Нет данных</div>
            )}
          </div>
          
          {/* Кнопка сохранения */}
          {calcResult && (
            <button
              onClick={handleSave}
              style={{
                marginTop: '1rem',
                padding: '0.5rem 1rem',
                background: '#16a34a',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '1rem'
              }}
            >
              💾 Сохранить в базу
            </button>
          )}
        </div>
        
        {/* Правая колонка */}
        <div>
          {/* Панель распределения */}
          <div style={{ padding: '1rem', background: '#fff', borderRadius: '8px', border: '1px solid #e5e7eb' }}>
            <h3>💰 Распределение суммы</h3>
            <div style={{ marginBottom: '0.5rem' }}>
              <label style={{ display: 'block', marginBottom: '0.25rem', fontWeight: '500' }}>
                Сумма:
              </label>
              <input
                type="number"
                value={totalAmount}
                onChange={(e) => setTotalAmount(e.target.value)}
                step="0.01"
                min="0"
                style={{
                  width: '100%',
                  padding: '0.5rem',
                  borderRadius: '4px',
                  border: '1px solid #ccc',
                  fontSize: '1rem'
                }}
              />
            </div>
            <button
              onClick={handleDistribute}
              disabled={loading || selectedIds.length === 0}
              style={{
                width: '100%',
                padding: '0.5rem',
                backgroundColor: loading || selectedIds.length === 0 ? '#9ca3af' : '#2563eb',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: loading || selectedIds.length === 0 ? 'not-allowed' : 'pointer',
                fontSize: '1rem',
                fontWeight: '500'
              }}
            >
              {loading ? '⏳ Выполняется...' : '🚀 Выполнить'}
            </button>
            <div style={{ marginTop: '0.5rem', fontSize: '0.8rem', color: '#666' }}>
              Выбрано элементов: <strong>{selectedIds.length}</strong>
            </div>
          </div>
          
          {/* Список сохраненных расчетов (с кнопкой Загрузить - ЗАДАЧА 10) */}
          <div style={{ 
            marginTop: '1rem', 
            padding: '1rem', 
            background: '#fff', 
            borderRadius: '8px', 
            border: '1px solid #e5e7eb'
          }}>
            <h3>📊 Сохраненные расчеты ({savedList.length})</h3>
            {savedList.length === 0 ? (
              <div style={{ color: '#666' }}>Нет сохраненных расчетов</div>
            ) : (
              savedList.map((calc: any) => (
                <div key={calc.id} style={{ 
                  padding: '0.5rem', 
                  marginBottom: '0.5rem', 
                  background: '#f9fafb', 
                  borderRadius: '4px',
                  border: '1px solid #e5e7eb'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <div style={{ fontWeight: 'bold' }}>
                        #{calc.id} - {calc.total_amount.toFixed(2)} ₽
                      </div>
                      <div style={{ fontSize: '0.8rem', color: '#666' }}>
                        {new Date(calc.created_at).toLocaleString()}
                      </div>
                    </div>
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                      <button
                        onClick={() => loadSavedCalculation(calc.id)}
                        style={{
                          padding: '0.25rem 0.5rem',
                          background: '#2563eb',
                          color: 'white',
                          border: 'none',
                          borderRadius: '4px',
                          cursor: 'pointer',
                          fontSize: '0.8rem'
                        }}
                      >
                        📂 Загрузить
                      </button>
                      <button
                        onClick={() => handleExport(calc.id)}
                        style={{
                          padding: '0.25rem 0.5rem',
                          background: '#16a34a',
                          color: 'white',
                          border: 'none',
                          borderRadius: '4px',
                          cursor: 'pointer',
                          fontSize: '0.8rem'
                        }}
                      >
                        📥 Excel
                      </button>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
