import React from 'react';
import ActiveIncidents from './components/ActiveIncidents';
import ActiveRequestsByType from './components/ActiveRequestsByType';
import ActiveIncidentsByAge from './components/ActiveIncidentsByAge';
import ActiveIncidentsByPriority from './components/ActiveIncidentsByPriority';
import IncidentsTrendLast10days from './components/IncidentsTrendLast10days';
import ActiveIncidentsByServiceType from './components/ActiveIncidentsByServiceType';
import ActiveServiceRequestsByAge from './components/ActiveServiceRequestsByAge';
import ActiveServiceRequestsBySeverity from './components/ActiveServiceRequestsBySeverity';
import ServiceRequestsTrendLast10days from './components/ServiceRequestsTrendLast10days';

function Dashboard() {
    return (
        <div>
            <h2>Dashboard</h2>
            <div>
                
            <div style={{width:'300px',backgroundColor:'#fff', maxHeight:'200px', margin:'10px 10px 10px 0px',float:'left',paddingRight:'5px'}}><ActiveIncidents /></div>
            <div style={{width:'300px',backgroundColor:'#fff', maxHeight:'200px', margin:'10px',float:'left',paddingRight:'5px'}}><ActiveRequestsByType /></div>
            <div style={{width:'300px',backgroundColor:'#fff', maxHeight:'200px', margin:'10px',float:'left',paddingRight:'5px'}}><ActiveIncidentsByAge /></div>
            
            </div>
            <div class="dassboardImgpadding">
            <div style={{width:'300px',backgroundColor:'#fff', maxHeight:'200px', margin:'10px 10px 10px 0px',float:'left',paddingRight:'5px'}}><ActiveIncidentsByPriority /></div>
            <div style={{width:'300px',backgroundColor:'#fff', maxHeight:'200px', margin:'10px',float:'left',paddingRight:'5px'}}><IncidentsTrendLast10days /></div>
            <div style={{width:'300px',backgroundColor:'#fff', maxHeight:'200px', margin:'10px',float:'left',paddingRight:'5px'}}><ActiveIncidentsByServiceType /></div>
            </div>
            <div class="dassboardImgpadding">
            <div style={{width:'300px',backgroundColor:'#fff', maxHeight:'200px', margin:'10px 10px 10px 0px',float:'left',paddingRight:'5px', overflow:'hidden'}}><ActiveServiceRequestsByAge /></div>
            <div style={{width:'300px',backgroundColor:'#fff', maxHeight:'200px', margin:'10px',float:'left',paddingRight:'5px', overflow:'hidden'}}><ActiveServiceRequestsBySeverity /></div>
            <div style={{width:'300px',backgroundColor:'#fff', maxHeight:'200px', margin:'10px',float:'left',paddingRight:'5px', overflow:'hidden'}}><ServiceRequestsTrendLast10days /></div>
            </div>
        </div>
    );
}

export default Dashboard;

