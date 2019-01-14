import java.util.concurrent.atomic.AtomicLong

USER_DIR = System.getProperty('user.working_dir','.') + '/'
DATA_DIR = USER_DIR + "outputs/"
TX_CSV = DATA_DIR + "tx_list.csv"
ALERT_CSV = DATA_DIR + "alerts.csv"
PROP_FILE = "janusgraph.properties"

println "Start loading transactions from " + TX_CSV

counter = new AtomicLong()
batchSize = 100000
cache = [:]
graph = JanusGraphFactory.open(PROP_FILE)


// create schema
mgmt = graph.openManagement()
// vertex schema
mgmt.makePropertyKey('vid').dataType(String.class).make()
mgmt.makePropertyKey('vtype').dataType(String.class).make()
mgmt.makePropertyKey('category').dataType(String.class).make()
mgmt.makePropertyKey('case').dataType(Boolean.class).make()
// edge schema
mgmt.makeEdgeLabel('account').make()
mgmt.makeEdgeLabel('transaction').make()
mgmt.makePropertyKey('tkey').dataType(String.class).make()

vid = mgmt.getPropertyKey('vid')
mgmt.buildIndex('vertexID',Vertex.class).addKey(vid).buildCompositeIndex()
mgmt.commit()

mutate = { ->
    if (0 == counter.incrementAndGet() % batchSize) {
        graph.tx().commit()
    }
}

addVertex = { def vid, def vtype, def category, def caseFlag ->
    if(!cache.containsKey(vid)){
        v = graph.addVertex("vid", vid, "vtype", vtype, "category", category, "case", caseFlag)
        mutate()
        cache[vid] = v
        return v
    }
    return cache[vid]
}


DEFAULT_INDEX = -1
case_set = new HashSet()
line_counter = new AtomicLong()

/*
 * Load Alert CSV File
 */
println "START LOAD ALERT FILE " + ALERT_CSV
// ALERT_KEY,ALERT_TEXT,ACCOUNT_ID,CUSTOMER_ID,EVENT_DATE,CHECK_NAME,Organization_Type,Escalated_To_Case_Investigation
alert_id = "ALERT_KEY"
account_id = "ACCOUNT_ID"
customer_id = "CUSTOMER_ID"
escalated = "Escalated_To_Case_Investigation"

alert_idx = DEFAULT_INDEX
acct_idx = DEFAULT_INDEX
cust_idx = DEFAULT_INDEX
escalated_idx = DEFAULT_INDEX

reader = new BufferedReader(new FileReader(ALERT_CSV))

line = reader.readLine()
fields = line.split(',', -1)
for(int i=0; i<fields.length; i++){
    switch(fields[i].replace("\"", "")){
        case alert_id: alert_idx = i; break
        case account_id: acct_idx = i; break
        case customer_id: cust_idx = i; break
        case escalated: escalated_idx = i; break
    }
}
println "---- Column indices of Alert CSV ----"
println "\t" + alert_id + ":" + alert_idx
println "\t" + account_id + ":" + acct_idx
println "\t" + customer_id + ":" + cust_idx
println "\t" + escalated + ":" + escalated_idx

while (true) {
    line = reader.readLine()
    if (0 == line_counter.incrementAndGet() % batchSize) {
        println line_counter
    }
    if (line == null) {
        break
    }
    data = line.split(',',-1)

    alertID = data[alert_idx].replaceAll("\\s", "")
    accountID = data[acct_idx].replaceAll("\\s", "")
    customerID = data[cust_idx].replaceAll("\\s", "")
    escalatedFlag = data[escalated_idx].replaceAll("\\s", "")

    if(escalatedFlag.toLowerCase() == "yes"){
        case_set.add(customerID)
    }
}
println "CASE Size: " + case_set.size()


/*
 * Load Transaction CSV File
 */
println "START LOAD TRANSACTION FILE: ${new Date()}"
// TXN_ID,ACCOUNT_ID,COUNTER_PARTY_ACCOUNT_NUM,TXN_SOURCE_TYPE_CODE,tx_count,TXN_AMOUNT_ORIG,start,end
orig_id = "ACCOUNT_ID"
dest_id = "COUNTER_PARTY_ACCOUNT_NUM"
tx_id = "TXN_ID"
amount = "TXN_AMOUNT_ORIG"
date = "RUN_DATE"
type = "TXN_SOURCE_TYPE_CODE"

orig_idx = DEFAULT_INDEX
dest_idx = DEFAULT_INDEX
tx_idx = DEFAULT_INDEX
amt_idx = DEFAULT_INDEX
date_idx = DEFAULT_INDEX
type_idx = DEFAULT_INDEX

reader = new BufferedReader(new FileReader(TX_CSV))

line = reader.readLine()
fields = line.split(',', -1)
for(int i=0; i<fields.length; i++){
    switch(fields[i].replace("\"", "")){
        case orig_id: orig_idx = i; break
        case dest_id: dest_idx = i; break
        case tx_id: tx_idx = i; break
        case amount: amt_idx = i; break
        case date: date_idx = i; break
        case type: type_idx = i; break
    }
}
println "---- Column indices of Transaction CSV ----"
println "\t" + orig_id + ":" + orig_idx
println "\t" + dest_id + ":" + dest_idx
println "\t" + tx_id + ":" + tx_idx
println "\t" + amount + ":" + amt_idx
println "\t" + date + ":" + date_idx
println "\t" + type + ":" + type_idx


while (true) {
    line = reader.readLine()
    if (0 == line_counter.incrementAndGet() % batchSize) {
        println line_counter
    }
    if (line == null) {
        break
    }
    data = line.split(',',-1)

    origID = data[orig_idx].replaceAll("\\s", "")
    destID = data[dest_idx].replaceAll("\\s", "")
    origV = cache[origID]
    destV = cache[destID]

    if(origV != null && destV != null) {
        origV.addEdge("transaction", destV, "tkey", tx_id)
    }
}

graph.tx().commit()
graph.close()
System.exit(0)
