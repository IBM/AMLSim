package amlsim.obsolete;

import it.unimi.dsi.webgraph.BVGraph;
import it.unimi.dsi.webgraph.algo.*;
import java.io.*;

public class HyperANFDist {

    public static void main(String[] args) {

        if(args.length != 4){
            System.err.println("Args: <basename> <logexp> <numthreads> <max-distance>");
            System.exit(1);
        }

        try{
            PrintWriter resultWriter = new PrintWriter(new FileWriter("result.log", true));
            resultWriter.println("\n----" + args[0]);

            long start = System.currentTimeMillis();
            BVGraph graph = BVGraph.load(args[0], 2);
            int connectedNodes = graph.numNodes();
            System.out.println("Nodes: " + connectedNodes);
            int log2m = Integer.parseInt(args[1]);
            int th = Integer.parseInt(args[2]);
            double aver = 0.0;

            HyperBall hyperanf = new HyperBall(graph,null,log2m,null,th,0,0,false);
            hyperanf.init();
            int DISTANCE = Integer.parseInt(args[3]);
            int prev = connectedNodes;
            for(int i=0; i<DISTANCE; i++){
                hyperanf.iterate();
                int mod = hyperanf.modified();
                int num = prev - mod;

                if(i == 0){
                    connectedNodes -= num;
                }else{
                    aver += i * (double)num / connectedNodes;
                }

                System.out.println(i + " " + mod + " " + aver);
                prev = mod;
                if(mod == 0){
                    System.out.println("Diameter: " + i);
                    resultWriter.println("Diameter: " + i);
                    break;
                }
            }
            System.out.println("Average Distance: " + aver);
            resultWriter.println("Average Distance: " + aver);

            hyperanf.close();
            resultWriter.close();
            long end = System.currentTimeMillis();
            System.out.println("Elapsed Time: " + (end - start)/1000 + "s");
        }catch (IOException e){
            e.printStackTrace();
        }
    }

}

