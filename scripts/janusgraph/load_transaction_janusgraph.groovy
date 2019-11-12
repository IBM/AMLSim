import java.util.concurrent.atomic.AtomicLong

USER_DIR = System.getProperty('user.working_dir','.') + '/'
DATA_DIR = USER_DIR + "outputs/"
ACCT_CSV = DATA_DIR + "accounts.csv"
TX_CSV = DATA_DIR + "tx.csv"
PROP_FILE = USER_DIR + "janusgraph.properties"


println "Open JanusGraph database from " + PROP_FILE
counter = new AtomicLong()
batchSize = 100000
cache = [:]
graph = JanusGraphFactory.open(PROP_FILE)



// create schema
mgmt = graph.openManagement()
// vertex schema
// ACCOUNT_ID,CUSTOMER_ID,INIT_BALANCE,COUNTRY,ACCOUNT_TYPE,IS_SAR,TX_BEHAVIOR_ID
mgmt.makePropertyKey('acct_id').dataType(String.class).make()  // ACCOUNT_ID
mgmt.makePropertyKey('cust_id').dataType(String.class).make()  // CUSTOMER_ID
mgmt.makePropertyKey('init_amount').dataType(Float.class).make()  // INIT_BALANCE
mgmt.makePropertyKey('country').dataType(String.class).make()  // COUNTRY
mgmt.makePropertyKey('acct_type').dataType(String.class).make()  // ACCOUNT_TYPE
mgmt.makePropertyKey('is_sar_acct').dataType(Boolean.class).make()  // IS_SAR
mgmt.makePropertyKey('behavior_id').dataType(Long.class).make()  // TX_BEHAVIOR_ID

// edge schema
// TX_ID,SENDER_ACCOUNT_ID,RECEIVER_ACCOUNT_ID,TX_TYPE,TX_AMOUNT,TIMESTAMP,IS_SAR,ALERT_ID
mgmt.makeEdgeLabel('edgelabel').make()
mgmt.makePropertyKey('tx_id').dataType(String.class).make()  // TX_ID
mgmt.makePropertyKey('tx_type').dataType(String.class).make()  // TX_TYPE
mgmt.makePropertyKey('amount').dataType(Float.class).make()  // TX_AMOUNT
mgmt.makePropertyKey('date').dataType(Long.class).make()  // TIMESTAMP
mgmt.makePropertyKey('is_sar_tx').dataType(Boolean.class).make()  // IS_SAR
mgmt.makePropertyKey('alert_id').dataType(Long.class).make()  // ALERT_ID
mgmt.commit()

mutate = { ->
    if (0 == counter.incrementAndGet() % batchSize) {
        graph.tx().commit()
    }
}

addVertex = { def acct, def cust, def amt, def country, def type, def is_sar, def behavior ->
    if(!cache.containsKey(acct)){
        v = graph.addVertex("acct_id", acct, "cust_id", cust, "init_amount", amt,
                "country", country, "acct_type", type, "is_sar_acct", is_sar, "behavior_id", behavior)
        mutate()
        cache[acct] = v
    }
}

setProperty = {def placeholder, def label, def key, def value ->
    cache[label].property(key, value)
    mutate()
}


/**
 * Load account list (vertices)
 * ACCOUNT_ID,CUSTOMER_ID,INIT_BALANCE,COUNTRY,ACCOUNT_TYPE,IS_SAR,TX_BEHAVIOR_ID
 */
println "Start loading accounts from " + ACCT_CSV
line_counter = new AtomicLong()
reader = new BufferedReader(new FileReader(ACCT_CSV))

DEFAULT_INDEX = -1
acct_idx = DEFAULT_INDEX
cust_idx = DEFAULT_INDEX
amt_idx = DEFAULT_INDEX
country_idx = DEFAULT_INDEX
type_idx = DEFAULT_INDEX
sar_idx = DEFAULT_INDEX
behavior_idx = DEFAULT_INDEX


// read the header
line = reader.readLine()
fields = line.split(',', -1)
for(int i=0; i<fields.length; i++){
    switch(fields[i]){
        case "ACCOUNT_ID": acct_idx = i; break
        case "CUSTOMER_ID": cust_idx = i; break
        case "INIT_BALANCE": amt_idx = i; break
        case "COUNTRY": country_idx = i; break
        case "ACCOUNT_TYPE": type_idx = i; break
        case "IS_SAR": sar_idx = i; break
        case "TX_BEHAVIOR_ID": behavior_idx = i; break
    }
}

println "---- Account Column Indices ----"
println "\tAccount ID: " + acct_idx
println "\tCustomer ID: " + cust_idx
println "\tInitial Balance: " + amt_idx
println "\tCountry: " + country_idx
println "\tAccount Type: " + type_idx
println "\tSAR Flag: " + sar_idx
println "\tBehavior ID: " + behavior_idx

while (true){
    line = reader.readLine()
    if (line_counter.incrementAndGet() % batchSize == 0) {
        println line_counter
    }
    if(line == null){
        break
    }

    fields = line.split(',', -1)
    acct_id = fields[acct_idx]
    cust_id = fields[cust_idx]
    init_amt = fields[amt_idx].toFloat()
    country = fields[country_idx]
    acct_type = fields[type_idx]
    is_sar = fields[sar_idx].toBoolean()
    behavior_id = fields[behavior_idx].toLong()

    addVertex(acct_id, cust_id, init_amt, country, acct_type, is_sar, behavior_id)
}


/**
 * Load transaction list (edges)
 * TX_ID,SENDER_ACCOUNT_ID,RECEIVER_ACCOUNT_ID,TX_TYPE,TX_AMOUNT,TIMESTAMP,IS_SAR,ALERT_ID
 */
// for each line in csv parsed, build the vertex and edge
println "Start loading transactions from " + TX_CSV
line_counter = new AtomicLong()
reader = new BufferedReader(new FileReader(TX_CSV))

// Column index
DEFAULT_INDEX = -1
txid_idx = DEFAULT_INDEX
orig_idx = DEFAULT_INDEX
dest_idx = DEFAULT_INDEX
type_idx = DEFAULT_INDEX
amt_idx = DEFAULT_INDEX
date_idx = DEFAULT_INDEX
sar_idx = DEFAULT_INDEX
alert_idx = DEFAULT_INDEX


// read the header
line = reader.readLine()
fields = line.split(',', -1)
for(int i=0; i<fields.length; i++){
    switch(fields[i]){
        case "TX_ID": txid_idx = i; break
        case "SENDER_ACCOUNT_ID": orig_idx = i; break
        case "RECEIVER_ACCOUNT_ID": dest_idx = i; break
        case "TX_TYPE": type_idx = i; break
        case "TX_AMOUNT": amt_idx = i; break
        case "TIMESTAMP": date_idx = i; break
        case "IS_SAR": sar_idx = i; break
        case "ALERT_ID": alert_idx = i; break
    }
}

println "---- Transaction Column Indices ----"
println "\tTransaction ID: " + txid_idx
println "\tSender ID: " + orig_idx
println "\tReceiver ID: " + dest_idx
println "\tTransaction Type: " + type_idx
println "\tAmount: " + amt_idx
println "\tDate: " + date_idx
println "\tSAR Flag: " + sar_idx
println "\tAlert ID: " + alert_idx


while (true) {
    line = reader.readLine()
    if (0 == line_counter.incrementAndGet() % batchSize) {
        println line_counter
    }
    if (line == null) {
        break
    }
    //split line
    fields = line.split(',', -1)

    orig = fields[orig_idx].replaceAll("\\s", "")
    dest = fields[dest_idx].replaceAll("\\s", "")

    // add edges
    if(orig != "" && dest != ""){
        tx_id = fields[txid_idx]
        tx_type = fields[type_idx]
        amount = fields[amt_idx].toFloat()
        date = fields[date_idx].toLong()
        is_sar = fields[sar_idx].toBoolean()
        alert_id = fields[alert_idx].toLong()

        // Here is a difference than python version "key" -> "tkey" since "key" is protected value in namespace
        cache[orig].addEdge("edgelabel", cache[dest], "tx_id", tx_id, "tx_type", tx_type, "amount", amount, "date", date, "is_sar_tx", is_sar, "alert_id", alert_id)
        mutate()
    }
}

graph.tx().commit()

g = graph.traversal()
numV = g.V().count().next()
numE = g.E().count().next()
println "total vertices added: ${numV}"
println "total edges added: ${numE}"
g.close()
graph.close()
System.exit(0)



