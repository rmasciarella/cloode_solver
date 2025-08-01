// Schedule Viewer - JavaScript for rendering Gantt chart visualization

class ScheduleViewer {
    constructor() {
        this.data = null;
        this.svg = null;
        this.xScale = null;
        this.yScale = null;
        this.zoom = null;
        this.margin = { top: 60, right: 200, bottom: 60, left: 150 };
        this.width = 0;
        this.height = 0;
        
        this.initializeEventListeners();
    }
    
    initializeEventListeners() {
        // File upload
        document.getElementById('uploadBtn').addEventListener('click', () => {
            document.getElementById('fileInput').click();
        });
        
        document.getElementById('fileInput').addEventListener('change', (e) => {
            this.loadFile(e.target.files[0]);
        });
        
        // Export button
        document.getElementById('exportBtn').addEventListener('click', () => {
            this.exportAsPNG();
        });
        
        // Zoom controls
        document.getElementById('zoomIn').addEventListener('click', () => {
            this.zoomIn();
        });
        
        document.getElementById('zoomOut').addEventListener('click', () => {
            this.zoomOut();
        });
        
        document.getElementById('zoomReset').addEventListener('click', () => {
            this.resetZoom();
        });
        
        // View controls
        document.getElementById('showLabels').addEventListener('change', (e) => {
            this.toggleLabels(e.target.checked);
        });
        
        document.getElementById('showGrid').addEventListener('change', (e) => {
            this.toggleGrid(e.target.checked);
        });
        
        // Window resize
        window.addEventListener('resize', () => {
            if (this.data) {
                this.renderChart();
            }
        });
    }
    
    async loadFile(file) {
        try {
            const text = await file.text();
            const data = JSON.parse(text);
            this.data = data;
            this.processData();
            this.updateMetadata();
            this.updateWarnings();
            this.updateMachineStats();
            this.renderChart();
            
            // Enable export button
            document.getElementById('exportBtn').disabled = false;
            
            // Show panels
            document.getElementById('metadataPanel').classList.remove('hidden');
            if (data.warnings && data.warnings.length > 0) {
                document.getElementById('warningsPanel').classList.remove('hidden');
            }
            document.getElementById('machineStats').classList.remove('hidden');
            
        } catch (error) {
            alert('Error loading file: ' + error.message);
        }
    }
    
    processData() {
        // Sort machines by ID
        this.data.machines.sort((a, b) => a.machine_id - b.machine_id);
        
        // Sort tasks by machine and start time
        this.data.tasks.sort((a, b) => {
            if (a.machine_id !== b.machine_id) {
                return a.machine_id - b.machine_id;
            }
            return a.start_time - b.start_time;
        });
        
        // Calculate concurrent tasks for each machine
        this.calculateConcurrency();
    }
    
    calculateConcurrency() {
        // Group tasks by machine
        const machineGroups = {};
        this.data.tasks.forEach(task => {
            if (!machineGroups[task.machine_id]) {
                machineGroups[task.machine_id] = [];
            }
            machineGroups[task.machine_id].push(task);
        });
        
        // Calculate lane assignment for concurrent tasks
        Object.keys(machineGroups).forEach(machineId => {
            const tasks = machineGroups[machineId];
            const lanes = [];
            
            tasks.forEach(task => {
                // Find first available lane
                let laneIndex = 0;
                for (let i = 0; i < lanes.length; i++) {
                    const laneEnd = Math.max(...lanes[i].map(t => t.end_time));
                    if (task.start_time >= laneEnd) {
                        laneIndex = i;
                        break;
                    } else if (i === lanes.length - 1) {
                        laneIndex = lanes.length;
                    }
                }
                
                if (!lanes[laneIndex]) {
                    lanes[laneIndex] = [];
                }
                lanes[laneIndex].push(task);
                task.lane = laneIndex;
            });
            
            // Store max lanes for this machine
            const machine = this.data.machines.find(m => m.machine_id == machineId);
            if (machine) {
                machine.maxLanes = lanes.length;
            }
        });
    }
    
    updateMetadata() {
        document.getElementById('totalJobs').textContent = this.data.metadata.total_jobs;
        document.getElementById('totalTasks').textContent = this.data.metadata.total_tasks;
        document.getElementById('makespan').textContent = 
            `${this.data.metadata.makespan} units (${this.formatTime(this.data.metadata.makespan)})`;
        document.getElementById('solveTime').textContent = 
            `${this.data.metadata.solve_time.toFixed(3)}s`;
    }
    
    updateWarnings() {
        const warningsList = document.getElementById('warningsList');
        warningsList.innerHTML = '';
        
        if (this.data.warnings && this.data.warnings.length > 0) {
            this.data.warnings.forEach(warning => {
                const li = document.createElement('li');
                li.textContent = warning;
                warningsList.appendChild(li);
            });
        }
    }
    
    updateMachineStats() {
        const statsList = document.getElementById('machineStatsList');
        statsList.innerHTML = '';
        
        this.data.machines.forEach(machine => {
            const statItem = document.createElement('div');
            statItem.className = 'machine-stat-item';
            
            const name = document.createElement('div');
            name.className = 'machine-stat-name';
            name.textContent = `${machine.machine_name} (Cap: ${machine.capacity})`;
            
            const utilization = document.createElement('div');
            utilization.className = 'machine-stat-utilization';
            
            const bar = document.createElement('div');
            bar.className = 'utilization-bar';
            
            const fill = document.createElement('div');
            fill.className = 'utilization-fill';
            fill.style.width = `${machine.utilization_percentage}%`;
            
            const label = document.createElement('span');
            label.className = 'utilization-label';
            label.textContent = `${machine.utilization_percentage}%`;
            
            bar.appendChild(fill);
            utilization.appendChild(bar);
            utilization.appendChild(label);
            
            statItem.appendChild(name);
            statItem.appendChild(utilization);
            statsList.appendChild(statItem);
        });
    }
    
    renderChart() {
        // Clear existing chart
        const container = document.getElementById('ganttContainer');
        container.querySelector('.empty-state').classList.add('hidden');
        
        const existingChart = document.getElementById('ganttChart');
        existingChart.innerHTML = '';
        existingChart.classList.remove('hidden');
        
        // Calculate dimensions
        const containerRect = container.getBoundingClientRect();
        this.width = containerRect.width - this.margin.left - this.margin.right;
        this.height = Math.max(400, this.calculateChartHeight()) - this.margin.top - this.margin.bottom;
        
        // Create SVG
        this.svg = d3.select('#ganttChart')
            .attr('width', containerRect.width)
            .attr('height', this.height + this.margin.top + this.margin.bottom);
        
        // Create main group with margins
        const mainGroup = this.svg.append('g')
            .attr('transform', `translate(${this.margin.left},${this.margin.top})`);
        
        // Create scales
        this.createScales();
        
        // Create grid
        this.createGrid(mainGroup);
        
        // Create axes
        this.createAxes(mainGroup);
        
        // Create chart content
        const chartGroup = mainGroup.append('g')
            .attr('class', 'chart-content');
        
        // Create zoom behavior
        this.zoom = d3.zoom()
            .scaleExtent([0.5, 5])
            .translateExtent([[-100, -100], [this.width + 100, this.height + 100]])
            .on('zoom', (event) => {
                chartGroup.attr('transform', event.transform);
                // Update grid on zoom
                mainGroup.select('.grid-x').call(
                    d3.axisBottom(this.xScale.copy().domain(
                        event.transform.rescaleX(this.xScale).domain()
                    ))
                    .tickSize(this.height)
                    .tickFormat('')
                );
            });
        
        this.svg.call(this.zoom);
        
        // Render tasks
        this.renderTasks(chartGroup);
        
        // Create legend
        this.createLegend();
    }
    
    calculateChartHeight() {
        let totalHeight = 0;
        this.data.machines.forEach(machine => {
            const laneHeight = 40;
            const lanes = machine.maxLanes || 1;
            totalHeight += Math.max(50, lanes * laneHeight + 10);
        });
        return totalHeight + this.margin.top + this.margin.bottom;
    }
    
    createScales() {
        // X scale (time)
        const maxTime = this.data.metadata.horizon || 100;
        this.xScale = d3.scaleLinear()
            .domain([0, maxTime])
            .range([0, this.width]);
        
        // Y scale (machines)
        let yPosition = 0;
        const machinePositions = {};
        
        this.data.machines.forEach(machine => {
            const laneHeight = 40;
            const lanes = machine.maxLanes || 1;
            const machineHeight = Math.max(50, lanes * laneHeight + 10);
            
            machinePositions[machine.machine_id] = {
                start: yPosition,
                height: machineHeight,
                lanes: lanes
            };
            
            yPosition += machineHeight;
        });
        
        this.machinePositions = machinePositions;
        this.totalHeight = yPosition;
    }
    
    createGrid(group) {
        // X grid
        const xGrid = group.append('g')
            .attr('class', 'grid grid-x')
            .attr('transform', `translate(0,${this.totalHeight})`)
            .call(d3.axisBottom(this.xScale)
                .tickSize(-this.totalHeight)
                .tickFormat(''));
        
        // Y grid (machine separators)
        const yGrid = group.append('g')
            .attr('class', 'grid grid-y');
        
        Object.values(this.machinePositions).forEach(pos => {
            yGrid.append('line')
                .attr('x1', 0)
                .attr('x2', this.width)
                .attr('y1', pos.start + pos.height)
                .attr('y2', pos.start + pos.height)
                .attr('stroke', '#e0e0e0')
                .attr('stroke-width', 1);
        });
    }
    
    createAxes(group) {
        // X axis
        const xAxis = d3.axisBottom(this.xScale)
            .tickFormat(d => `${d}`);
        
        group.append('g')
            .attr('class', 'axis axis-x')
            .attr('transform', `translate(0,${this.totalHeight})`)
            .call(xAxis);
        
        // X axis label
        group.append('text')
            .attr('class', 'axis-label')
            .attr('text-anchor', 'middle')
            .attr('x', this.width / 2)
            .attr('y', this.totalHeight + 40)
            .text('Time Units');
        
        // Y axis (machine labels)
        const yAxis = group.append('g')
            .attr('class', 'axis axis-y');
        
        this.data.machines.forEach(machine => {
            const pos = this.machinePositions[machine.machine_id];
            const yPos = pos.start + pos.height / 2;
            
            yAxis.append('text')
                .attr('class', 'machine-label')
                .attr('text-anchor', 'end')
                .attr('x', -10)
                .attr('y', yPos)
                .attr('dy', '0.35em')
                .text(`${machine.machine_name} (${machine.capacity})`);
        });
    }
    
    renderTasks(group) {
        const taskGroups = group.selectAll('.task-group')
            .data(this.data.tasks)
            .enter()
            .append('g')
            .attr('class', 'task-group');
        
        // Task rectangles
        taskGroups.append('rect')
            .attr('class', 'task-rect')
            .attr('x', d => this.xScale(d.start_time))
            .attr('y', d => {
                const machinePos = this.machinePositions[d.machine_id];
                const laneHeight = 35;
                const laneOffset = d.lane * laneHeight + 5;
                return machinePos.start + laneOffset;
            })
            .attr('width', d => this.xScale(d.end_time) - this.xScale(d.start_time))
            .attr('height', 30)
            .attr('fill', d => d.color)
            .attr('stroke', d => d3.color(d.color).darker())
            .attr('stroke-width', 1)
            .attr('rx', 3)
            .on('mouseenter', (event, d) => this.showTooltip(event, d))
            .on('mouseleave', () => this.hideTooltip());
        
        // Task labels
        taskGroups.append('text')
            .attr('class', 'task-label')
            .attr('x', d => this.xScale(d.start_time) + 5)
            .attr('y', d => {
                const machinePos = this.machinePositions[d.machine_id];
                const laneHeight = 35;
                const laneOffset = d.lane * laneHeight + 5;
                return machinePos.start + laneOffset + 15;
            })
            .attr('dy', '0.35em')
            .text(d => {
                const maxWidth = this.xScale(d.end_time) - this.xScale(d.start_time) - 10;
                const fullText = `${d.job_name}-${d.task_name}`;
                // Simple text truncation
                if (maxWidth < 50) return '';
                if (maxWidth < 100) return d.task_name;
                return fullText;
            })
            .attr('pointer-events', 'none');
    }
    
    createLegend() {
        const legendData = {};
        this.data.tasks.forEach(task => {
            if (!legendData[task.job_id]) {
                legendData[task.job_id] = {
                    id: task.job_id,
                    name: task.job_name,
                    color: task.color
                };
            }
        });
        
        const legendItems = Object.values(legendData).sort((a, b) => a.id - b.id);
        
        const legend = this.svg.append('g')
            .attr('class', 'legend')
            .attr('transform', `translate(${this.width + this.margin.left + 20}, ${this.margin.top})`);
        
        legend.append('text')
            .attr('class', 'legend-title')
            .attr('x', 0)
            .attr('y', -10)
            .text('Jobs');
        
        const legendItem = legend.selectAll('.legend-item')
            .data(legendItems)
            .enter()
            .append('g')
            .attr('class', 'legend-item')
            .attr('transform', (d, i) => `translate(0, ${i * 25 + 10})`);
        
        legendItem.append('rect')
            .attr('width', 15)
            .attr('height', 15)
            .attr('fill', d => d.color)
            .attr('stroke', d => d3.color(d.color).darker())
            .attr('rx', 2);
        
        legendItem.append('text')
            .attr('x', 20)
            .attr('y', 7.5)
            .attr('dy', '0.35em')
            .text(d => d.name);
    }
    
    showTooltip(event, task) {
        const tooltip = document.getElementById('tooltip');
        
        const content = `
            <div class="tooltip-header">${task.job_name} - ${task.task_name}</div>
            <div class="tooltip-row">
                <span class="tooltip-label">Machine:</span>
                <span class="tooltip-value">${task.machine_name}</span>
            </div>
            <div class="tooltip-row">
                <span class="tooltip-label">Start:</span>
                <span class="tooltip-value">${task.start_time} (${this.formatTime(task.start_time)})</span>
            </div>
            <div class="tooltip-row">
                <span class="tooltip-label">End:</span>
                <span class="tooltip-value">${task.end_time} (${this.formatTime(task.end_time)})</span>
            </div>
            <div class="tooltip-row">
                <span class="tooltip-label">Duration:</span>
                <span class="tooltip-value">${task.duration} units</span>
            </div>
        `;
        
        tooltip.innerHTML = content;
        tooltip.classList.remove('hidden');
        
        // Position tooltip
        const rect = event.target.getBoundingClientRect();
        tooltip.style.left = rect.left + rect.width / 2 + 'px';
        tooltip.style.top = rect.top - 10 + 'px';
    }
    
    hideTooltip() {
        document.getElementById('tooltip').classList.add('hidden');
    }
    
    toggleLabels(show) {
        d3.selectAll('.task-label')
            .style('display', show ? 'block' : 'none');
    }
    
    toggleGrid(show) {
        d3.selectAll('.grid')
            .style('display', show ? 'block' : 'none');
    }
    
    zoomIn() {
        this.svg.transition().call(this.zoom.scaleBy, 1.3);
    }
    
    zoomOut() {
        this.svg.transition().call(this.zoom.scaleBy, 0.7);
    }
    
    resetZoom() {
        this.svg.transition().call(this.zoom.transform, d3.zoomIdentity);
    }
    
    exportAsPNG() {
        const svgElement = document.getElementById('ganttChart');
        const svgString = new XMLSerializer().serializeToString(svgElement);
        
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        const img = new Image();
        
        const svgBlob = new Blob([svgString], { type: 'image/svg+xml;charset=utf-8' });
        const url = URL.createObjectURL(svgBlob);
        
        img.onload = () => {
            canvas.width = svgElement.width.baseVal.value * 2;
            canvas.height = svgElement.height.baseVal.value * 2;
            ctx.scale(2, 2);
            ctx.fillStyle = 'white';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            ctx.drawImage(img, 0, 0);
            
            canvas.toBlob((blob) => {
                const link = document.createElement('a');
                link.href = URL.createObjectURL(blob);
                link.download = `schedule_${new Date().toISOString().slice(0, 10)}.png`;
                link.click();
            });
            
            URL.revokeObjectURL(url);
        };
        
        img.src = url;
    }
    
    formatTime(timeUnits) {
        const hours = Math.floor(timeUnits * 15 / 60);
        const minutes = (timeUnits * 15) % 60;
        if (minutes === 0) {
            return `${hours}h`;
        }
        return `${hours}h ${minutes}m`;
    }
}

// Initialize viewer when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ScheduleViewer();
});