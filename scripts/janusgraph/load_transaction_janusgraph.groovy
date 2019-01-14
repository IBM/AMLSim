import java.time.LocalDate
import java.time.format.DateTimeFormatter
import java.util.concurrent.atomic.AtomicLong

USER_DIR = System.getProperty('user.working_dir','.') + '/'
DATA_DIR = USER_DIR + "outputs/"
TX_CSV = DATA_DIR + "tx.csv"
CASE_CSV = DATA_DIR + "case_accts.csv"
PROP_FILE = "janusgraph.properties"

println "Start loading transactions from " + TX_CSV

counter = new AtomicLong()
batchSize = 100000
cache = [:]
graph = JanusGraphFactory.open(PROP_FILE)


case_file = new File(CASE_CSV)
case_set = case_file.readLines().toSet()


// create schema
mgmt = graph.openManagement()
// vertex schema
mgmt.makePropertyKey('acct').dataType(String.class).make()
mgmt.makePropertyKey('name').dataType(String.class).make()
mgmt.makePropertyKey('city').dataType(String.class).make()
mgmt.makePropertyKey('state').dataType(String.class).make()
mgmt.makePropertyKey('country').dataType(String.class).make()
mgmt.makePropertyKey('address').dataType(String.class).make()
mgmt.makePropertyKey('sar').dataType(Boolean.class).make()
mgmt.makePropertyKey('start_day').dataType(Long.class).make()
mgmt.makePropertyKey('end_day').dataType(Long.class).make()
// edge schema
mgmt.makeEdgeLabel('edgelabel').make()
mgmt.makePropertyKey('tkey').dataType(String.class).make()
mgmt.makePropertyKey('orig_addr').dataType(String.class).make()
mgmt.makePropertyKey('bene_addr').dataType(String.class).make()
mgmt.makePropertyKey('amount').dataType(Float.class).make()
mgmt.makePropertyKey('date').dataType(String.class).make()
mgmt.makePropertyKey('tid').dataType(Boolean.class).make()
mgmt.makePropertyKey('alert').dataType(Boolean.class).make()
mgmt.commit()

mutate = { ->
    if (0 == counter.incrementAndGet() % batchSize) {
        graph.tx().commit()
    }
}

addVertex = { def acct, def sar ->
    if(!cache.containsKey(acct)){
        name = acct
        city = acct + "_city"
        state = acct + "_state"
        country = acct + "_country"
        address = acct + "_addr"
        v = graph.addVertex("acct", acct, "name", name, "city", city, "state", state, "country", country, "address", address, "sar", sar)
        mutate()
        cache[acct] = v
    }
}

setProperty = {def placeholder, def label, def key, def value ->
    cache[label].property(key, value)
    mutate()
}

getDays= { def date ->
    return date.toInteger()
}

// for each line in csvparsed, build the vertex and edge
line_counter = new AtomicLong()
reader = new BufferedReader(new FileReader(TX_CSV))

// Column index
DEFAULT_INDEX = -1

orig_idx = DEFAULT_INDEX
dest_idx = DEFAULT_INDEX
transactionID_idx = DEFAULT_INDEX
amount_idx = DEFAULT_INDEX
date_idx = DEFAULT_INDEX


// read the header
line = reader.readLine()
fields = line.split(',', -1)
for(int i=0; i<fields.length; i++){
    switch(fields[i]){
        case "ACCOUNT_ID": orig_idx = i; break
        case "COUNTER_PARTY_ACCOUNT_NUM": dest_idx = i; break
        case "TXN_ID": transactionID_idx = i; break
        case "TXN_AMOUNT_ORIG": amount_idx = i; break
        case "start": date_idx = i; break
    }
}

println "---- Column indices ----"
println "\tOrig: " + orig_idx
println "\tDest: " + dest_idx
println "\tTranNo: " + transactionID_idx
println "\tBaseAmt: " + amount_idx
println "\tValueDate: " + date_idx



while (true) {
    line = reader.readLine()
    if (0 == line_counter.incrementAndGet() % batchSize) {
        println line_counter
    }
    if (line == null) {
        break
    }
    //split line
    line = line.split(',',-1)

    orig = line[dest_idx].replaceAll("\\s", "")
    bene = line[dest_idx].replaceAll("\\s", "")

    // add vertex
    if(orig != ""){
        if(case_set.contains(orig)){
            addVertex(orig, true)
        }else{
            addVertex(orig, false)
        }
    }
    if(bene != ""){
        if(case_set.contains(bene)){
            addVertex(bene, true)
        }else{
            addVertex(bene, false)
        }
    }
    // add edges
    if(orig != "" && bene != ""){
        transaction_ID = line[transactionID_idx]  // 0
        amount = line[amount_idx].toFloat()  // 5
        date = line[date_idx]  // 10
        // Here is a difference than python version "key" -> "tkey" since "key" is protected value in namespace
        cache[orig].addEdge("edgelabel", cache[bene], "tkey", transaction_ID, "orig_addr", orig, "bene_addr", bene, "amount", amount, "date", date, "tid", transaction_ID, "alert", "")
        mutate()
        days = getDays(date)
        START = "start_day"
        END = "end_day"

        orig_start = cache[orig].property(START)
        orig_end = cache[orig].property(END)
        if(orig_start.isPresent() == false || days < orig_start.value()){
            setProperty("label", orig, START, days)
        }
        if(orig_end.isPresent() == false || days > orig_end.value()){
            setProperty("label", orig, END, days)
        }

        bene_start = cache[bene].property(START)
        bene_end = cache[bene].property(END)
        if(bene_start.isPresent() == false || days < bene_start.value()){
            setProperty("label", bene, START, days)
        }
        if(bene_end.isPresent() == false || days > bene_end.value()){
            setProperty("label", bene, END, days)
        }
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






