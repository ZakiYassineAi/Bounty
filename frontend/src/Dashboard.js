import React, { useState, useEffect } from 'react';
import { Table, Button, message, Select, Row, Col, Card } from 'antd';
import axios from 'axios';

const { Option } = Select;

const Dashboard = () => {
  const [targets, setTargets] = useState([]);
  const [evidence, setEvidence] = useState([]);
  const [filteredTargets, setFilteredTargets] = useState([]);
  const [statusFilter, setStatusFilter] = useState(null);
  const [severityFilter, setSeverityFilter] = useState(null);

  useEffect(() => {
    axios.get('/targets/')
      .then(response => {
        setTargets(response.data);
        setFilteredTargets(response.data);
      })
      .catch(error => {
        message.error('Failed to fetch targets');
        console.error(error);
      });
  }, []);

  useEffect(() => {
    const params = {};
    if (statusFilter) {
      params.status = statusFilter;
    }
    axios.get('/evidence/', { params })
      .then(response => {
        setEvidence(response.data);
      })
      .catch(error => {
        message.error('Failed to fetch evidence');
        console.error(error);
      });
  }, [statusFilter]);

  useEffect(() => {
    let newFilteredTargets = [...targets];

    const evidenceToFilter = severityFilter
      ? evidence.filter(e => e.severity === severityFilter)
      : evidence;

    if (statusFilter || severityFilter) {
        const targetIds = [...new Set(evidenceToFilter.map(e => e.target_id))];
        newFilteredTargets = newFilteredTargets.filter(t => targetIds.includes(t.id));
    }


    setFilteredTargets(newFilteredTargets);
  }, [severityFilter, targets, evidence, statusFilter]);

  const handleExport = (targetId) => {
    axios({
      url: `/api/reports/export/${targetId}`,
      method: 'GET',
      responseType: 'blob', // Important
    }).then((response) => {
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `target_report_${targetId}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    }).catch(error => {
      message.error('Failed to export report');
      console.error(error);
    });
  };

  const columns = [
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: 'URL',
      dataIndex: 'url',
      key: 'url',
    },
    {
      title: 'Scope',
      dataIndex: 'scope',
      key: 'scope',
      render: scope => scope.join(', '),
    },
    {
      title: 'Action',
      key: 'action',
      render: (text, record) => (
        <Button type="primary" onClick={() => handleExport(record.id)}>Export</Button>
      ),
    },
  ];

  return (
    <div style={{ padding: '20px' }}>
      <h1>Dashboard</h1>
      <Card style={{ marginBottom: 16 }}>
        <Row gutter={16}>
          <Col>
            <Select
              placeholder="Filter by status"
              onChange={value => setStatusFilter(value)}
              style={{ width: 200 }}
              allowClear
            >
              <Option value="new">New</Option>
              <Option value="in-progress">In Progress</Option>
              <Option value="resolved">Resolved</Option>
            </Select>
          </Col>
          <Col>
            <Select
              placeholder="Filter by severity"
              onChange={value => setSeverityFilter(value)}
              style={{ width: 200 }}
              allowClear
            >
              <Option value="critical">Critical</Option>
              <Option value="high">High</Option>
              <Option value="medium">Medium</Option>
              <Option value="low">Low</Option>
              <Option value="info">Info</Option>
            </Select>
          </Col>
        </Row>
      </Card>
      <Table dataSource={filteredTargets} columns={columns} rowKey="id" />
    </div>
  );
};

export default Dashboard;
