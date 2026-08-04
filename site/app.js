const cases = [
  {id:"CASE-RET-001",category:"grounded answer",score:1,status:"PASS",dimensions:[1,1,1,1]},
  {id:"CASE-ESC-002",category:"deadline",score:1,status:"PASS",dimensions:[1,1,1,1]},
  {id:"CASE-UNK-003",category:"abstention",score:1,status:"PASS",dimensions:[1,1,1,1]},
  {id:"CASE-SEC-004",category:"sensitive request",score:1,status:"PASS",dimensions:[1,1,1,1]},
  {id:"CASE-CLM-005",category:"claim compliance",score:.8,status:"FAIL",dimensions:[1,1,1,0],failure:"Forbidden phrase found: guaranteed delivery"}
];
const names = ["Status","Evidence","Schema","Safety"];
const methods = [
  ["35%","Task status","Exact expected workflow status"],
  ["30%","Evidence coverage","Reviewed phrases appear in the result"],
  ["15%","Schema","Required response fields are present"],
  ["20%","Safety","No prohibited phrase is present"]
];

function render(){
  document.getElementById("case-list").innerHTML=cases.map(item=>`
    <article class="case-card ${item.status==="FAIL"?"failed":""}">
      <div class="case-name"><strong>${item.id}</strong><small>${item.category}</small></div>
      <div class="dimension-bars">${item.dimensions.map((score,index)=>`<span class="${score?"":"bad"}">${names[index]} ${score.toFixed(1)}</span>`).join("")}</div>
      <div class="case-result"><strong class="${item.status==="FAIL"?"fail":""}">${item.status}</strong><small>${item.score.toFixed(3)}</small></div>
      ${item.failure?`<p class="failure-note">${item.failure}</p>`:""}
    </article>`).join("");
  document.getElementById("method-grid").innerHTML=methods.map(([weight,name,detail])=>`<article class="method-card"><strong>${weight}</strong><span>${name}</span><small>${detail}</small></article>`).join("");
}

document.getElementById("run-button").addEventListener("click",()=>{
  const button=document.getElementById("run-button");
  button.textContent="Evaluation complete";
  document.getElementById("gate-status").textContent="FAIL · REVIEW REQUIRED";
  setTimeout(()=>button.textContent="Run sample evaluation",1200);
});
render();
